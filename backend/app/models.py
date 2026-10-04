"""Curated drug record (spec §5.2).

This model is the source of truth. `data/schema/drug.schema.json` is generated
from it with `python -m backend.app.validate_data --write-schema`, and a test
fails if the two drift apart.

The vocabularies below are closed. Adding a value means editing spec §5.2 first.
"""

from datetime import date
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---- Closed vocabularies (spec §5.2, §6.3) ----

Organ = Literal[
    "brain", "heart", "lungs", "liver", "stomach", "intestines", "kidneys", "pancreas",
    "blood_vessels", "muscle", "skin", "fat", "thyroid", "spleen", "bladder",
]
EnzymeRole = Literal["substrate", "inhibitor", "inducer"]
Strength = Literal["strong", "moderate", "weak"]
Importance = Literal["major", "minor"]
VdUnit = Literal["L/kg", "L"]
EliminationRoute = Literal["kidney", "bile", "other"]
JourneyStepName = Literal["absorption", "distribution", "metabolism", "action", "elimination"]
EffectCategory = Literal[
    "anticoagulant", "bleeding_risk", "serotonergic", "lowers_blood_pressure",
    "raises_potassium", "nsaid", "lowers_seizure_threshold", "sedation",
]
CurationStatus = Literal["draft", "verified"]

ORGANS: tuple[str, ...] = get_args(Organ)
EFFECT_CATEGORIES: tuple[str, ...] = get_args(EffectCategory)

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class StrictModel(BaseModel):
    """Rejects unknown fields so typos and unlisted keys don't slip through."""

    model_config = ConfigDict(extra="forbid")


class Source(StrictModel):
    dailymed_setid: str = Field(pattern=UUID_PATTERN, description="DailyMed label set ID")
    section: str = Field(pattern=r"^\d+(\.\d+)*$", description='Label section, e.g. "2" or "12.3"')


# ---- PK values: label range + the single value used for the curve ----


class PkValue(StrictModel):
    range: tuple[float, float]
    model: float = Field(gt=0)
    source: Source

    @model_validator(mode="after")
    def check_range(self):
        low, high = self.range
        if not 0 < low <= high:
            raise ValueError("range must be [low, high] with 0 < low <= high")
        if not low <= self.model <= high:
            raise ValueError("model value must fall inside range")
        return self


class Bioavailability(PkValue):
    unit: Literal["fraction"]

    @model_validator(mode="after")
    def check_fraction(self):
        if self.range[1] > 1:
            raise ValueError("bioavailability is a fraction and can't exceed 1")
        return self


class HalfLife(PkValue):
    unit: Literal["h"]


class Vd(PkValue):
    unit: VdUnit


class Tmax(PkValue):
    unit: Literal["h"]


class Pk(StrictModel):
    bioavailability: Bioavailability
    half_life: HalfLife
    vd: Vd
    tmax: Tmax


class DoseRange(StrictModel):
    min: float = Field(gt=0)
    max: float = Field(gt=0)
    typical: float = Field(gt=0)
    intervals_h: list[float] = Field(min_length=1)
    source: Source

    @model_validator(mode="after")
    def check_order(self):
        if not self.min <= self.typical <= self.max:
            raise ValueError("dose must satisfy min <= typical <= max")
        if any(interval <= 0 for interval in self.intervals_h):
            raise ValueError("dosing intervals must be greater than 0 hours")
        return self


class Formulation(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    label: str = Field(min_length=1)
    route: str = Field(min_length=1)
    dose_mg: DoseRange
    pk: Pk


# ---- Enzymes, transporters, effects, elimination, journey ----


class EnzymeEntry(StrictModel):
    """Also used for transporters (spec §6.1: same rule)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "allOf": [
                {"if": {"properties": {"role": {"const": "substrate"}}},
                 "then": {"required": ["importance"],
                          "properties": {"importance": {"type": "string"}}}},
                {"if": {"properties": {"role": {"enum": ["inhibitor", "inducer"]}}},
                 "then": {"required": ["strength"],
                          "properties": {"strength": {"type": "string"}}}},
            ]
        },
    )

    name: str = Field(min_length=1)
    role: EnzymeRole
    strength: Strength | None = None
    importance: Importance | None = None
    source: Source

    @model_validator(mode="after")
    def check_conditional_fields(self):
        if self.role == "substrate" and self.importance is None:
            raise ValueError("substrate entries need importance (major or minor)")
        if self.role in ("inhibitor", "inducer") and self.strength is None:
            raise ValueError(f"{self.role} entries need strength (strong, moderate or weak)")
        return self


class Effect(StrictModel):
    category: EffectCategory
    source: Source


class EliminationRouteEntry(StrictModel):
    route: EliminationRoute
    fraction: float = Field(ge=0, le=1)
    unchanged_fraction: float | None = Field(default=None, ge=0, le=1)


class Elimination(StrictModel):
    routes: list[EliminationRouteEntry] = Field(min_length=1)
    source: Source

    @model_validator(mode="after")
    def check_total(self):
        if sum(route.fraction for route in self.routes) > 1 + 1e-9:
            raise ValueError("elimination route fractions add up to more than 1")
        return self


class JourneyStep(StrictModel):
    step: JourneyStepName
    organ: Organ
    text: str = Field(min_length=1)


# ---- Top-level record ----


class Names(StrictModel):
    generic: str = Field(min_length=1)
    brands: list[str]


class Ids(StrictModel):
    rxcui: str = Field(pattern=r"^\d+$")
    chembl: str = Field(pattern=r"^CHEMBL\d+$")
    pubchem_cid: int = Field(gt=0)


class Curation(StrictModel):
    reviewed_by: str = Field(min_length=1)
    reviewed_on: date
    status: CurationStatus


class Drug(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    names: Names
    ids: Ids
    common_use: str = Field(min_length=1)
    formulations: list[Formulation] = Field(min_length=1)
    enzymes: list[EnzymeEntry]
    transporters: list[EnzymeEntry]
    effects: list[Effect]
    elimination: Elimination
    journey: list[JourneyStep] = Field(min_length=1)
    curation: Curation


def drug_json_schema() -> dict:
    schema = Drug.model_json_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$comment": "Generated from backend/app/models.py. Do not edit by hand; run "
                    "`python -m backend.app.validate_data --write-schema`.",
        **schema,
    }
