"""ChEMBL lookups: mechanism/targets for any drug (spec §4, §5.1).

Name -> ChEMBL molecule ID falls back to EBI UniChem's PubChem->ChEMBL mapping
when a direct name match fails -- the same two-step resolution as
backend/scripts/curation_lookup.py's dev tool, just production-shaped: never
raises on a resolvable gap, just returns fewer targets. A single bad
mechanism/target entry is skipped rather than failing the whole list, since
ChEMBL's target endpoint is observably flaky (confirmed while building this).
"""

import httpx

from backend.app.services.cache import cached_fetch

CHEMBL_BASE = "https://www.ebi.ac.uk/chembl/api/data"
UNICHEM_BASE = "https://www.ebi.ac.uk/unichem/api/v1/compounds"
# ChEMBL's mechanism/target endpoints were observed to hang (not fail fast) during
# development -- a cold request could chain 3 upstream calls (molecule, mechanism,
# target), so a generous per-call timeout compounds into tens of seconds of a
# blocked page load. Kept short since a slow-but-real response is rarer than a
# hung one, and targets degrade to [] gracefully either way.
TIMEOUT = 6


class UpstreamError(Exception):
    pass


def _get_json(url: str, params: dict | None = None) -> dict:
    try:
        response = httpx.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise UpstreamError(str(exc)) from exc


def _post_json(url: str, body: dict) -> dict:
    try:
        response = httpx.post(url, json=body, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise UpstreamError(str(exc)) from exc


def resolve_chembl_id(generic_name: str, pubchem_cid: int | None) -> str | None:
    def fetch_by_name():
        return _get_json(f"{CHEMBL_BASE}/molecule.json", {"pref_name__iexact": generic_name})

    try:
        data, _ = cached_fetch("chembl", f"molecule_by_name:{generic_name.lower()}", fetch_by_name)
        molecules = data.get("molecules") or []
        if molecules:
            return molecules[0]["molecule_chembl_id"]
    except UpstreamError:
        pass

    if not pubchem_cid:
        return None

    def fetch_unichem():
        return _post_json(UNICHEM_BASE, {"type": "sourceID", "compound": str(pubchem_cid), "sourceID": 22})

    try:
        data, _ = cached_fetch("unichem", f"pubchem_to_chembl:{pubchem_cid}", fetch_unichem)
    except UpstreamError:
        return None
    ids = sorted({s["compoundId"] for c in data.get("compounds", []) for s in c["sources"]
                  if s["shortName"] == "chembl"})
    return ids[0] if len(ids) == 1 else None


def _mechanisms(molecule_chembl_id: str) -> list[dict]:
    def fetch():
        return _get_json(f"{CHEMBL_BASE}/mechanism.json", {"molecule_chembl_id": molecule_chembl_id})
    data, _ = cached_fetch("chembl", f"mechanism:{molecule_chembl_id}", fetch)
    return data.get("mechanisms") or []


def _target(target_chembl_id: str) -> dict | None:
    def fetch():
        return _get_json(f"{CHEMBL_BASE}/target.json", {"target_chembl_id": target_chembl_id})
    data, _ = cached_fetch("chembl", f"target:{target_chembl_id}", fetch)
    targets = data.get("targets") or []
    return targets[0] if targets else None


def fetch_targets(generic_name: str, pubchem_cid: int | None) -> list[dict]:
    chembl_id = resolve_chembl_id(generic_name, pubchem_cid)
    if not chembl_id:
        return []

    try:
        mechanisms = _mechanisms(chembl_id)
    except UpstreamError:
        return []

    targets = []
    for mech in mechanisms:
        target_chembl_id = mech.get("target_chembl_id")
        if not target_chembl_id:
            continue
        try:
            target = _target(target_chembl_id)
        except UpstreamError:
            continue
        if not target:
            continue

        components = target.get("target_components") or []
        uniprot = next((c["accession"] for c in components if c.get("accession")), None)
        gene = next(
            (syn["component_synonym"] for c in components
             for syn in c.get("target_component_synonyms") or []
             if syn.get("syn_type") == "GENE_SYMBOL"),
            None,
        )
        targets.append({
            "chembl_id": target_chembl_id,
            "uniprot": uniprot,
            "gene": gene,
            "name": target.get("pref_name"),
            "action": (mech.get("action_type") or "").lower() or None,
            "plain_description": mech.get("mechanism_of_action"),
        })
    return targets
