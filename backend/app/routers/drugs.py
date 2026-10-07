from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from backend.app.api_models import CuratedSummary, DrugBundle
from backend.app.services import drug_store, pubchem

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

    try:
        molecule = pubchem.fetch_properties(drug.ids.pubchem_cid)
    except pubchem.UpstreamError:
        molecule = None

    return DrugBundle(
        rxcui=drug.ids.rxcui,
        generic=drug.names.generic,
        brands=drug.names.brands,
        molecule=molecule,
        curated=drug.model_dump(mode="json"),
    )


@router.get("/drugs/{rxcui}/structure.sdf")
def get_structure_sdf(rxcui: str) -> PlainTextResponse:
    drug = drug_store.get_by_rxcui(rxcui)
    if drug is None:
        raise HTTPException(404, "We couldn't find that drug.")
    try:
        sdf = pubchem.fetch_structure_sdf(drug.ids.pubchem_cid)
    except pubchem.UpstreamError:
        raise HTTPException(502, "Couldn't load the molecule structure right now.")
    return PlainTextResponse(sdf, media_type="chemical/x-mdl-sdfile")
