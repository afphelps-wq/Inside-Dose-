"""Interaction checking: the enzyme/transporter rule and the effect-pair rule (spec §6.1).

Only `verified` drugs (spec §5.2) are checked; draft or uncurated drugs land in
`unchecked` instead.
"""

import json
from itertools import combinations
from pathlib import Path

from backend.app.models import Drug, Source
from backend.app.services.drug_store import get_by_rxcui

REPO_ROOT = Path(__file__).resolve().parents[3]
EFFECT_PAIRS_PATH = REPO_ROOT / "data" / "rules" / "effect_pairs.json"

SEVERITY_ORDER = {"major": 0, "moderate": 1, "minor": 2}

ENZYME_SEVERITY = {
    ("strong", "major"): "major",
    ("strong", "minor"): "moderate",
    ("moderate", "major"): "moderate",
    ("moderate", "minor"): "minor",
    ("weak", "major"): "minor",
    ("weak", "minor"): "minor",
}

_EFFECT_PAIRS: list[dict] = json.loads(EFFECT_PAIRS_PATH.read_text())


def _source_dict(source: Source) -> dict:
    return source.model_dump(exclude_none=True)


def _enzyme_findings(a: Drug, b: Drug) -> list[dict]:
    findings = []
    for regulator, substrate_drug in ((a, b), (b, a)):
        for reg in regulator.enzymes + regulator.transporters:
            if reg.role not in ("inhibitor", "inducer"):
                continue
            for sub in substrate_drug.enzymes + substrate_drug.transporters:
                if sub.role != "substrate" or sub.name != reg.name:
                    continue
                severity = ENZYME_SEVERITY[(reg.strength, sub.importance)]
                verb = "inhibits" if reg.role == "inhibitor" else "induces"
                effect_verb = "raise" if reg.role == "inhibitor" else "lower"
                findings.append({
                    "drugs": [regulator.ids.rxcui, substrate_drug.ids.rxcui],
                    "type": "enzyme",
                    "severity": severity,
                    "mechanism": (
                        f"{regulator.names.generic.capitalize()} {reg.strength}ly {verb} {reg.name}, "
                        f"which breaks down {substrate_drug.names.generic}."
                    ),
                    "plain_message": (
                        f"{regulator.names.generic.capitalize()} can {effect_verb} "
                        f"{substrate_drug.names.generic} levels in the blood."
                    ),
                    "sources": [_source_dict(reg.source), _source_dict(sub.source)],
                })
    return findings


def _effect_findings(a: Drug, b: Drug) -> list[dict]:
    findings = []
    cats_a = {e.category: e for e in a.effects}
    cats_b = {e.category: e for e in b.effects}
    for rule in _EFFECT_PAIRS:
        ca, cb = rule["category_a"], rule["category_b"]
        if ca in cats_a and cb in cats_b:
            left, right, cat_left, cat_right = a, b, ca, cb
        elif cb in cats_a and ca in cats_b:
            left, right, cat_left, cat_right = a, b, cb, ca
        else:
            continue
        findings.append({
            "drugs": [left.ids.rxcui, right.ids.rxcui],
            "type": "effect",
            "severity": rule["severity"],
            "mechanism": (
                f"{left.names.generic.capitalize()} ({cat_left.replace('_', ' ')}) and "
                f"{right.names.generic.capitalize()} ({cat_right.replace('_', ' ')}) can combine."
            ),
            "plain_message": rule["plain_message"],
            "sources": [_source_dict(cats_a[cat_left].source), _source_dict(cats_b[cat_right].source)],
        })
    return findings


def check_interactions(rxcuis: list[str]) -> dict:
    drugs: dict[str, Drug] = {}
    unchecked: list[str] = []
    for rxcui in rxcuis:
        drug = get_by_rxcui(rxcui)
        if drug is None or drug.curation.status != "verified":
            unchecked.append(rxcui)
        else:
            drugs[rxcui] = drug

    findings = []
    for rxcui_a, rxcui_b in combinations(drugs, 2):
        a, b = drugs[rxcui_a], drugs[rxcui_b]
        findings += _enzyme_findings(a, b)
        findings += _effect_findings(a, b)

    findings.sort(key=lambda finding: SEVERITY_ORDER[finding["severity"]])
    return {"findings": findings, "unchecked": unchecked}
