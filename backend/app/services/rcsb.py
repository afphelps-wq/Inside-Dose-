"""RCSB PDB lookups for the Targets tab's Mol* view (spec §4, §5.1).

Finds solved structures for a target (by UniProt accession) and, when the
drug resolves to a PDB chemical component via an exact chemical-structure
match, flags which of those structures actually have the drug bound --
not just the target alone.
"""

import httpx

from backend.app.services.cache import cached_fetch

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
DATA_BASE = "https://data.rcsb.org/rest/v1/core"
TIMEOUT = 15
MAX_STRUCTURES = 10


class UpstreamError(Exception):
    pass


def _search(query: dict, return_type: str) -> list[str]:
    try:
        response = httpx.post(
            SEARCH_URL, json={"query": query, "return_type": return_type,
                               "request_options": {"paginate": {"rows": 50}}},
            timeout=TIMEOUT,
        )
        if response.status_code == 404:  # RCSB's "no results" response
            return []
        response.raise_for_status()
        return [r["identifier"] for r in response.json().get("result_set", [])]
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise UpstreamError(str(exc)) from exc


def ligand_id_for_inchi(inchi: str) -> str | None:
    """A drug's PDB chemical-component ID (e.g. apixaban -> 'GG2'), if PDB has one."""
    def fetch():
        ids = _search({
            "type": "terminal", "service": "chemical",
            "parameters": {"value": inchi, "type": "descriptor",
                            "descriptor_type": "InChI", "match_type": "graph-exact"},
        }, "mol_definition")
        return ids[0] if ids else None

    try:
        result, _ = cached_fetch("rcsb", f"ligand_for_inchi:{inchi}", fetch)
    except UpstreamError:
        return None
    return result


def _structures_for_uniprot(uniprot: str) -> list[str]:
    def fetch():
        return _search({
            "type": "terminal", "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match", "value": uniprot,
            },
        }, "entry")
    result, _ = cached_fetch("rcsb", f"structures_for_uniprot:{uniprot}", fetch)
    return result


def _structures_with_ligand(uniprot: str, ligand_id: str) -> set[str]:
    def fetch():
        return _search({
            "type": "group", "logical_operator": "and",
            "nodes": [
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                    "operator": "exact_match", "value": uniprot,
                }},
                {"type": "terminal", "service": "text", "parameters": {
                    "attribute": "rcsb_nonpolymer_entity_container_identifiers.nonpolymer_comp_id",
                    "operator": "exact_match", "value": ligand_id,
                }},
            ],
        }, "entry")
    result, _ = cached_fetch("rcsb", f"structures_with_ligand:{uniprot}:{ligand_id}", fetch)
    return set(result)


def entry_title(pdb_id: str) -> str:
    def fetch():
        try:
            response = httpx.get(f"{DATA_BASE}/entry/{pdb_id}", timeout=TIMEOUT)
            response.raise_for_status()
            return response.json().get("struct", {}).get("title") or pdb_id
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError(str(exc)) from exc
    try:
        title, _ = cached_fetch("rcsb", f"entry_title:{pdb_id}", fetch)
        return title
    except UpstreamError:
        return pdb_id


def structures_for_target(uniprot: str, inchi: str | None) -> list[dict]:
    try:
        all_ids = _structures_for_uniprot(uniprot)
    except UpstreamError:
        return []
    if not all_ids:
        return []

    with_drug: set[str] = set()
    if inchi:
        ligand_id = ligand_id_for_inchi(inchi)
        if ligand_id:
            try:
                with_drug = _structures_with_ligand(uniprot, ligand_id)
            except UpstreamError:
                with_drug = set()

    # Drug-bound structures always included -- the plain UniProt-only search
    # is capped and its default relevance ranking won't necessarily surface
    # them on its own (observed live: true for apixaban/factor Xa, the one
    # structure with the drug bound ranked outside the first 50 of 192).
    ordered = list(with_drug) + [pid for pid in all_ids if pid not in with_drug]
    ordered = ordered[:MAX_STRUCTURES]
    return [{"pdb_id": pid, "title": entry_title(pid), "has_this_drug": pid in with_drug} for pid in ordered]
