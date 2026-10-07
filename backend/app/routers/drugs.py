from fastapi import APIRouter, HTTPException

from backend.app.api_models import CuratedSummary, DrugBundle
from backend.app.services import drug_store

router = APIRouter()


@router.get("/drugs/curated", response_model=list[CuratedSummary])
def list_curated() -> list[CuratedSummary]:
    return [
        CuratedSummary(
            rxcui=drug.ids.rxcui,
            id=drug.id,
            generic=drug.names.generic,
            brands=drug.names.brands,
            common_use=drug.common_use,
        )
        for drug in drug_store.all_drugs()
    ]


@router.get("/drugs/{rxcui}", response_model=DrugBundle)
def get_drug(rxcui: str) -> DrugBundle:
    drug = drug_store.get_by_rxcui(rxcui)
    if drug is None:
        raise HTTPException(404, "We couldn't find that drug.")
    return DrugBundle(
        rxcui=drug.ids.rxcui,
        generic=drug.names.generic,
        brands=drug.names.brands,
        curated=drug.model_dump(mode="json"),
    )
