import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from backend.app.models import EFFECT_CATEGORIES, ORGANS, Drug
from backend.app.validate_data import DRUGS_DIR, SCHEMA_PATH, render_schema, validate_file, validate_record

# Fictional record used only to exercise the validator. These are NOT real drug values.
SOURCE = {"dailymed_setid": "00000000-0000-0000-0000-000000000000", "section": "2"}
VALID = {
    "id": "testdrug",
    "names": {"generic": "testdrug", "brands": ["Testbrand"]},
    "ids": {"rxcui": "1", "chembl": "CHEMBL1", "pubchem_cid": 1},
    "common_use": "Testing",
    "formulations": [{
        "id": "test_ir",
        "label": "Testdrug (immediate release)",
        "route": "oral",
        "dose_mg": {"min": 10, "max": 100, "typical": 20, "intervals_h": [12, 24], "source": SOURCE},
        "pk": {
            "bioavailability": {"range": [0.5, 0.7], "model": 0.6, "unit": "fraction", "source": SOURCE},
            "half_life": {"range": [4, 8], "model": 6, "unit": "h", "source": SOURCE},
            "vd": {"range": [1, 2], "model": 1.5, "unit": "L/kg", "source": SOURCE},
            "tmax": {"range": [1, 3], "model": 2, "unit": "h", "source": SOURCE},
        },
    }],
    "enzymes": [
        {"name": "CYP0A0", "role": "substrate", "importance": "major", "source": SOURCE},
        {"name": "CYP0B0", "role": "inhibitor", "strength": "strong", "source": SOURCE},
    ],
    "transporters": [],
    "effects": [{"category": "sedation", "source": SOURCE}],
    "elimination": {
        "routes": [
            {"route": "kidney", "fraction": 0.6, "unchanged_fraction": 0.1},
            {"route": "bile", "fraction": 0.4},
        ],
        "source": SOURCE,
    },
    "journey": [{"step": "absorption", "organ": "intestines", "text": "Test text."}],
    "curation": {"reviewed_by": "Test", "reviewed_on": "2026-01-01", "status": "draft"},
}

SCHEMA = json.loads(SCHEMA_PATH.read_text())


def mutate(path, value):
    """Copy of VALID with the value at `path` replaced (or deleted if value is DELETE)."""
    record = copy.deepcopy(VALID)
    target = record
    for key in path[:-1]:
        target = target[key]
    if value is DELETE:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return record


DELETE = object()
PK = ("formulations", 0, "pk")
DOSE = ("formulations", 0, "dose_mg")

# Each case breaks one rule. `in_schema` is False for cross-field rules that JSON Schema
# can't express; those are enforced by the Pydantic model only.
INVALID_CASES = [
    ("unknown enzyme role", ("enzymes", 0, "role"), "blocker", True),
    ("substrate missing importance", ("enzymes", 0, "importance"), DELETE, True),
    ("inhibitor missing strength", ("enzymes", 1, "strength"), DELETE, True),
    ("inhibitor strength null", ("enzymes", 1, "strength"), None, True),
    ("unknown strength", ("enzymes", 1, "strength"), "very strong", True),
    ("unknown effect category", ("effects", 0, "category"), "makes_sleepy", True),
    ("unknown journey organ", ("journey", 0, "organ"), "toe", True),
    ("unknown journey step", ("journey", 0, "step"), "digestion", True),
    ("unknown vd unit", (*PK, "vd", "unit"), "mL", True),
    ("wrong half-life unit", (*PK, "half_life", "unit"), "min", True),
    ("missing pk value", (*PK, "tmax"), DELETE, True),
    ("unknown elimination route", ("elimination", "routes", 0, "route"), "lungs", True),
    ("unknown curation status", ("curation", "status"), "done", True),
    ("unknown extra field", ("surprise",), 1, True),
    ("missing source", ("effects", 0, "source"), DELETE, True),
    ("placeholder setid", ("effects", 0, "source"), {"dailymed_setid": "<lookup>", "section": "2"}, True),
    ("placeholder rxcui", ("ids", "rxcui"), "<lookup>", True),
    ("no formulations", ("formulations",), [], True),
    ("no journey steps", ("journey",), [], True),
    ("model outside range", (*PK, "half_life", "model"), 9, False),
    ("range reversed", (*PK, "half_life", "range"), [8, 4], False),
    ("bioavailability above 1", (*PK, "bioavailability", "range"), [0.5, 1.2], False),
    ("typical dose above max", (*DOSE, "typical"), 200, False),
    ("elimination over 100%", ("elimination", "routes", 1, "fraction"), 0.5, False),
    ("bad review date", ("curation", "reviewed_on"), "last tuesday", False),
]


def test_valid_record_passes_both():
    assert validate_record(VALID) == []


@pytest.mark.parametrize("name,path,value,in_schema", INVALID_CASES, ids=[c[0] for c in INVALID_CASES])
def test_invalid_record_rejected(name, path, value, in_schema):
    record = mutate(path, value)
    with pytest.raises(ValidationError):
        Drug.model_validate(record)
    schema_errors = list(Draft202012Validator(SCHEMA).iter_errors(record))
    assert bool(schema_errors) == in_schema


def test_id_must_match_file_name():
    assert any(e.startswith("id:") for e in validate_record(VALID, expected_id="otherdrug"))


def test_schema_file_matches_model():
    assert SCHEMA_PATH.read_text() == render_schema(), (
        "drug.schema.json is out of date; run `python -m backend.app.validate_data --write-schema`"
    )


def test_vocabularies_match_spec():
    assert set(ORGANS) == {
        "brain", "heart", "lungs", "liver", "stomach", "intestines", "kidneys", "pancreas",
        "blood_vessels", "muscle", "skin", "fat", "thyroid", "spleen", "bladder",
    }
    assert set(EFFECT_CATEGORIES) == {
        "anticoagulant", "bleeding_risk", "serotonergic", "lowers_blood_pressure",
        "raises_potassium", "nsaid", "lowers_seizure_threshold", "sedation",
    }


DRUG_FILES = sorted(DRUGS_DIR.glob("*.json"))


@pytest.mark.skipif(not DRUG_FILES, reason="no curated drug files yet")
@pytest.mark.parametrize("path", DRUG_FILES, ids=[p.name for p in DRUG_FILES])
def test_curated_file_is_valid(path: Path):
    assert validate_file(path) == []
