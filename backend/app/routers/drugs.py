from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from backend.app.api_models import CuratedSummary, DrugBundle, SearchResult
from backend.app.models import Drug
from backend.app.services import chembl, drug_store, pubchem, rxnorm

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


@router.get("/search", response_model=list[SearchResult])
def search(q: str) -> list[SearchResult]:
    if not q.strip():
        return []
    results = rxnorm.search(q, limit=10)
    return [
        SearchResult(
            rxcui=r["rxcui"], generic=r["generic"], brand=r["brand"],
            curated=drug_store.get_by_rxcui(r["rxcui"]) is not None,
        )
        for r in results
    ]


def _resolve(rxcui: str) -> dict | None:
    """Either half of spec §4's drug bundle: a curated record, or a live
    RxNorm/PubChem/ChEMBL lookup (M6) for any other known rxcui."""
    drug = drug_store.get_by_rxcui(rxcui)
    if drug is not None:
        return {
            "rxcui": drug.ids.rxcui, "generic": drug.names.generic, "brands": drug.names.brands,
            "pubchem_cid": drug.ids.pubchem_cid, "curated": drug,
        }

    resolved = rxnorm.resolve_ingredient(rxcui)
    if resolved is None:
        return None
    cid = pubchem.resolve_cid_by_name(resolved["generic"])
    return {
        "rxcui": resolved["rxcui"], "generic": resolved["generic"], "brands": resolved["brands"],
        "pubchem_cid": cid, "curated": None,
    }


@router.get("/drugs/{rxcui}", response_model=DrugBundle)
def get_drug(rxcui: str) -> DrugBundle:
    info = _resolve(rxcui)
    if info is None:
        raise HTTPException(404, "We couldn't find that drug.")

    molecule = None
    if info["pubchem_cid"]:
        try:
            molecule = pubchem.fetch_properties(info["pubchem_cid"])
        except pubchem.UpstreamError:
            molecule = None

    curated: Drug | None = info["curated"]
    targets = [] if curated is not None else chembl.fetch_targets(info["generic"], info["pubchem_cid"])

    sources = []
    if curated is None:
        sources.append({"name": "RxNorm", "url": f"https://rxnav.nlm.nih.gov/REST/rxcui/{info['rxcui']}"})
        if molecule:
            sources.append({"name": "PubChem", "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{info['pubchem_cid']}"})
        if targets:
            sources.append({"name": "ChEMBL", "url": "https://www.ebi.ac.uk/chembl/"})

    return DrugBundle(
        rxcui=info["rxcui"],
        generic=info["generic"],
        brands=info["brands"],
        molecule=molecule,
        targets=targets,
        curated=curated.model_dump(mode="json") if curated is not None else None,
        sources=sources,
    )


@router.get("/drugs/{rxcui}/structure.sdf")
def get_structure_sdf(rxcui: str) -> PlainTextResponse:
    info = _resolve(rxcui)
    if info is None or not info["pubchem_cid"]:
        raise HTTPException(404, "We couldn't find a 3D structure for that drug.")
    try:
        sdf = pubchem.fetch_structure_sdf(info["pubchem_cid"])
    except pubchem.UpstreamError:
        raise HTTPException(502, "Couldn't load the molecule structure right now.")
    return PlainTextResponse(sdf, media_type="chemical/x-mdl-sdfile")
