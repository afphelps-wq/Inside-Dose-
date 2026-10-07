"""In-memory store of curated drug records, loaded once from data/drugs/*.json (spec §3.1)."""

import json

from backend.app.models import Drug
from backend.app.validate_data import DRUGS_DIR


def _load() -> dict[str, Drug]:
    drugs = {}
    for path in sorted(DRUGS_DIR.glob("*.json")):
        drug = Drug.model_validate(json.loads(path.read_text()))
        drugs[drug.ids.rxcui] = drug
    return drugs


_BY_RXCUI = _load()


def all_drugs() -> list[Drug]:
    return list(_BY_RXCUI.values())


def get_by_rxcui(rxcui: str) -> Drug | None:
    return _BY_RXCUI.get(rxcui)
