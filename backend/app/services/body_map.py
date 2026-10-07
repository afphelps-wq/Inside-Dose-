"""Aggregate per-target tissue expression into the 15-organ body_map (spec §6.3)."""

import json
import re
from pathlib import Path

from backend.app.services import hpa

REPO_ROOT = Path(__file__).resolve().parents[3]
TISSUE_MAP_PATH = REPO_ROOT / "data" / "hpa_tissue_map.json"
_TISSUE_MAP = json.loads(TISSUE_MAP_PATH.read_text())

_LEVEL_RANK = {"high": 3, "medium": 2, "low": 1}


def _normalize_tissue(name: str) -> str:
    return re.sub(r"\s+\d+$", "", name.strip().lower())


def build(targets: list[dict]) -> dict:
    """targets: a bundle's `targets` list (each needs a 'gene'). Returns
    {organ: {level, basis, targets: [gene, ...]}}; an organ with several
    tissues or targets keeps whichever gave it the highest level (spec §6.3)."""
    organs: dict[str, dict] = {}

    for target in targets:
        gene = target.get("gene")
        if not gene:
            continue
        for tissue_name, info in hpa.tissue_levels(gene).items():
            organ = _TISSUE_MAP.get(_normalize_tissue(tissue_name))
            if organ is None:
                continue
            existing = organs.get(organ)
            if existing is None or _LEVEL_RANK[info["level"]] > _LEVEL_RANK[existing["level"]]:
                organs[organ] = {"level": info["level"], "basis": info["basis"], "targets": [gene]}
            elif _LEVEL_RANK[info["level"]] == _LEVEL_RANK[existing["level"]] and gene not in existing["targets"]:
                existing["targets"].append(gene)

    return organs
