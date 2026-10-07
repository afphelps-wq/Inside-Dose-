"""PubChem PUG REST lookups for the Molecule tab (spec §5.1, §4).

Every call goes through the Postgres cache (spec §3.3) so repeat requests for
the same drug don't re-hit PubChem (M6: "cache hits on repeat"). With no
DATABASE_URL configured, cached_fetch degrades to a plain live call every time.
"""

import httpx

from backend.app.services.cache import cached_fetch
from backend.app.services.http_client import get_client

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 10


class UpstreamError(Exception):
    """PubChem didn't return usable data (network failure, 4xx/5xx, bad body)."""


def _fetch_structure_sdf(cid: int) -> str:
    """3D SDF if PubChem has a conformer, else 2D (spec §7: no 3D -> 2D fallback)."""
    for record_type in ("3d", "2d"):
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/SDF?record_type={record_type}"
        try:
            response = get_client().get(url, timeout=TIMEOUT)
        except httpx.HTTPError as exc:
            raise UpstreamError(str(exc)) from exc
        if response.status_code == 200 and response.text.strip():
            return response.text
    raise UpstreamError(f"PubChem has no 3D or 2D structure for CID {cid}")


def fetch_structure_sdf(cid: int) -> str:
    sdf, _ = cached_fetch("pubchem", f"sdf:{cid}", lambda: _fetch_structure_sdf(cid))
    return sdf


def _fetch_properties(cid: int) -> dict:
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight/JSON"
    try:
        response = httpx.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        props = response.json()["PropertyTable"]["Properties"][0]
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise UpstreamError(str(exc)) from exc
    return {
        "pubchem_cid": cid,
        "formula": props["MolecularFormula"],
        "weight": props["MolecularWeight"],
    }


def fetch_properties(cid: int) -> dict:
    properties, _ = cached_fetch("pubchem", f"properties:{cid}", lambda: _fetch_properties(cid))
    return properties


def fetch_inchi(cid: int) -> str | None:
    """For matching a drug to its PDB chemical-component ID (Targets tab Mol* view)."""
    def fetch():
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/property/InChI/JSON"
        try:
            response = get_client().get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()["PropertyTable"]["Properties"][0]["InChI"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise UpstreamError(str(exc)) from exc

    try:
        inchi, _ = cached_fetch("pubchem", f"inchi:{cid}", fetch)
        return inchi
    except UpstreamError:
        return None


def resolve_cid_by_name(name: str) -> int | None:
    """Live-lookup drugs (M6): resolve an ingredient name to a PubChem CID."""
    def fetch():
        url = f"{PUBCHEM_BASE}/compound/name/{name}/cids/JSON"
        try:
            response = get_client().get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise UpstreamError(str(exc)) from exc

    try:
        data, _ = cached_fetch("pubchem", f"cid_by_name:{name.lower()}", fetch)
        return data["IdentifierList"]["CID"][0]
    except (UpstreamError, KeyError, IndexError):
        return None
