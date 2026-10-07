"""PubChem PUG REST lookups for the Molecule tab (spec §5.1, §4).

M3 scope: calls PubChem directly, uncached. Spec rule #5 ("every external API
call goes through the backend") is satisfied -- the frontend never calls
PubChem itself -- but the Postgres cache table (spec §3.3) arrives in M6.
"""

import httpx

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
TIMEOUT = 10


class UpstreamError(Exception):
    """PubChem didn't return usable data (network failure, 4xx/5xx, bad body)."""


def fetch_structure_sdf(cid: int) -> str:
    """3D SDF if PubChem has a conformer, else 2D (spec §7: no 3D -> 2D fallback)."""
    for record_type in ("3d", "2d"):
        url = f"{PUBCHEM_BASE}/compound/cid/{cid}/SDF?record_type={record_type}"
        try:
            response = httpx.get(url, timeout=TIMEOUT)
        except httpx.HTTPError as exc:
            raise UpstreamError(str(exc)) from exc
        if response.status_code == 200 and response.text.strip():
            return response.text
    raise UpstreamError(f"PubChem has no 3D or 2D structure for CID {cid}")


def fetch_properties(cid: int) -> dict:
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
