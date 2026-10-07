"""RxNorm (NLM) lookups: search autocomplete + ingredient resolution (spec §4, §5.1).

The app's canonical drug ID is the RxNorm RxCUI of the *ingredient* (spec §4),
so both entry points here resolve whatever the API or the user gave us (a
brand, a specific dosage form, ...) up to that ingredient-level concept via
RxNorm's `allrelated` endpoint, which groups every related concept by term
type (tty) in one call: IN = ingredient, BN = brand name, SBD/SCD/... =
specific formulated products.
"""

import httpx

from backend.app.services.cache import cached_fetch

RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"
TIMEOUT = 10


class UpstreamError(Exception):
    pass


def _get_json(url: str, params: dict | None = None) -> dict:
    try:
        response = httpx.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise UpstreamError(str(exc)) from exc


def _approximate_candidates(query: str, max_entries: int = 20) -> list[dict]:
    def fetch():
        return _get_json(f"{RXNORM_BASE}/approximateTerm.json", {"term": query, "maxEntries": max_entries})
    data, _ = cached_fetch("rxnorm", f"approximate:{query.lower()}", fetch)
    return data.get("approximateGroup", {}).get("candidate") or []


def _all_related(rxcui: str) -> dict[str, list[dict]]:
    def fetch():
        return _get_json(f"{RXNORM_BASE}/rxcui/{rxcui}/allrelated.json")
    data, _ = cached_fetch("rxnorm", f"allrelated:{rxcui}", fetch)
    groups: dict[str, list[dict]] = {}
    for group in data.get("allRelatedGroup", {}).get("conceptGroup") or []:
        groups[group["tty"]] = group.get("conceptProperties") or []
    return groups


def properties(rxcui: str) -> dict | None:
    def fetch():
        return _get_json(f"{RXNORM_BASE}/rxcui/{rxcui}/properties.json")
    data, _ = cached_fetch("rxnorm", f"properties:{rxcui}", fetch)
    return data.get("properties")


def search(query: str, limit: int = 10) -> list[dict]:
    """Autocomplete: brand/generic name -> ingredient-level {rxcui, generic, brand}."""
    results = []
    seen_rxcuis = set()
    for candidate in _approximate_candidates(query, max_entries=max(20, limit * 2)):
        rxcui = candidate.get("rxcui")
        if not rxcui:
            continue
        try:
            groups = _all_related(rxcui)
        except UpstreamError:
            continue
        ingredients = groups.get("IN") or groups.get("PIN") or []
        if not ingredients:
            continue
        ingredient = ingredients[0]
        ing_rxcui = ingredient["rxcui"]
        if ing_rxcui in seen_rxcuis:
            continue
        seen_rxcuis.add(ing_rxcui)
        brands = groups.get("BN") or []
        results.append({
            "rxcui": ing_rxcui,
            "generic": ingredient["name"],
            "brand": brands[0]["name"] if brands else None,
        })
        if len(results) >= limit:
            break
    return results


def resolve_ingredient(rxcui: str) -> dict | None:
    """Any rxcui (brand, specific product, or already-ingredient) -> ingredient-level info."""
    try:
        groups = _all_related(rxcui)
    except UpstreamError:
        return None

    ingredients = groups.get("IN") or groups.get("PIN") or []
    if ingredients:
        ing_rxcui, name = ingredients[0]["rxcui"], ingredients[0]["name"]
    else:
        try:
            props = properties(rxcui)
        except UpstreamError:
            return None
        if not props or props.get("tty") not in ("IN", "PIN"):
            return None
        ing_rxcui, name = rxcui, props["name"]

    brands = groups.get("BN") or []
    return {"rxcui": ing_rxcui, "generic": name, "brands": [b["name"] for b in brands]}
