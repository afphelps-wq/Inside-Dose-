"""Response/request models for the API surface (spec §4). Separate from backend.app.models,
which is the curated drug record schema -- these are the wire shapes built on top of it.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CuratedSummary(BaseModel):
    rxcui: str
    id: str
    generic: str
    brands: list[str]
    common_use: str


class SearchResult(BaseModel):
    rxcui: str
    generic: str
    brand: str | None
    curated: bool


class DrugBundle(BaseModel):
    """M2 fills in `curated` only; molecule/targets/body_map arrive with live lookup (M6-M8)."""

    rxcui: str
    generic: str
    brands: list[str]
    molecule: dict | None = None
    targets: list = Field(default_factory=list)
    body_map: dict = Field(default_factory=dict)
    curated: dict | None = None
    stale: bool = False
    sources: list[dict] = Field(default_factory=list)


class TargetStructure(BaseModel):
    pdb_id: str
    title: str
    has_this_drug: bool


class InteractionRequest(BaseModel):
    rxcuis: list[str] = Field(min_length=2, max_length=5)


class InteractionFinding(BaseModel):
    drugs: list[str]
    type: Literal["enzyme", "effect"]
    severity: Literal["major", "moderate", "minor"]
    mechanism: str
    plain_message: str
    sources: list[dict]


class InteractionResult(BaseModel):
    findings: list[InteractionFinding]
    unchecked: list[str]
