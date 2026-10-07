"""Human Protein Atlas lookups for the Body tab (spec §5.1, §6.3).

HPA's public data no longer exposes the categorical per-tissue "High / Medium
/ Low / Not detected" IHC table spec originally assumed -- confirmed absent
from both their search API and the full bulk TSV download (checked directly
while building this, Oct 2026). What's available instead is a numeric
"specific" value per tissue -- "Protein tissue specific Intensity" / "RNA
tissue specific nTPM" -- listing only the handful of tissues where a gene is
notably enriched, not a full ~45-tissue readout.

Adaptation (see SPEC.md §6.3 for the full caveat): rank a gene's own listed
tissues against each other and bin into the same three levels, protein first
with an RNA fallback, matching spec's original design. A tissue HPA doesn't
list for a gene reads as "not detected" from this source -- which conflates
"truly absent" with "not notably enriched elsewhere" -- the real limitation
behind this whole adaptation.
"""

import httpx

from backend.app.services.cache import cached_fetch
from backend.app.services.http_client import get_client

HPA_BASE = "https://www.proteinatlas.org/api/search_download.php"
TIMEOUT = 15


class UpstreamError(Exception):
    pass


def _get_json(params: dict) -> list[dict]:
    try:
        response = get_client().get(HPA_BASE, params={**params, "format": "json", "compress": "no"}, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise UpstreamError(str(exc)) from exc


def _specific_values(gene_symbol: str) -> dict:
    """Raw {'protein': {tissue: float}, 'rna': {tissue: float}} for one gene, cached."""
    def fetch():
        rows = _get_json({"search": gene_symbol, "columns": "g,prtsm,rnatsm"})
        exact = next((r for r in rows if r.get("Gene", "").upper() == gene_symbol.upper()), None)
        if exact is None:
            return {"protein": {}, "rna": {}}
        protein = {k: float(v) for k, v in (exact.get("Protein tissue specific Intensity") or {}).items()}
        rna = {k: float(v) for k, v in (exact.get("RNA tissue specific nTPM") or {}).items()}
        return {"protein": protein, "rna": rna}

    data, _ = cached_fetch("hpa", f"specific:{gene_symbol.upper()}", fetch)
    return data


def _bin_by_rank(values: dict[str, float]) -> dict[str, str]:
    """Top third of a gene's own listed tissues -> high, etc. (see module docstring)."""
    if not values:
        return {}
    ranked = sorted(values, key=values.get, reverse=True)
    n = len(ranked)
    levels = {}
    for i, tissue in enumerate(ranked):
        if n == 1:
            levels[tissue] = "high"
        elif n == 2:
            levels[tissue] = "high" if i == 0 else "medium"
        else:
            frac = i / n
            levels[tissue] = "high" if frac < 1 / 3 else "medium" if frac < 2 / 3 else "low"
    return levels


def tissue_levels(gene_symbol: str) -> dict[str, dict]:
    """{tissue_name: {'level': 'high'|'medium'|'low', 'basis': 'protein'|'rna'}} for one gene."""
    try:
        values = _specific_values(gene_symbol)
    except UpstreamError:
        return {}

    if values["protein"]:
        return {t: {"level": lvl, "basis": "protein"} for t, lvl in _bin_by_rank(values["protein"]).items()}
    if values["rna"]:
        return {t: {"level": lvl, "basis": "rna"} for t, lvl in _bin_by_rank(values["rna"]).items()}
    return {}
