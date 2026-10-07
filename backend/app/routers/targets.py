from fastapi import APIRouter

from backend.app.api_models import TargetStructure
from backend.app.services import pubchem, rcsb
from backend.app.services.resolve import resolve as resolve_drug

router = APIRouter()


@router.get("/targets/{uniprot}/structures", response_model=list[TargetStructure])
def get_structures(uniprot: str, rxcui: str | None = None) -> list[TargetStructure]:
    """Solved PDB structures for a target, flagging which have the drug bound
    (spec §4, §5.1 Mol* view). `rxcui` is optional -- without it we still
    return the target's structures, just none flagged has_this_drug."""
    inchi = None
    if rxcui:
        info = resolve_drug(rxcui)
        if info and info["pubchem_cid"]:
            inchi = pubchem.fetch_inchi(info["pubchem_cid"])

    structures = rcsb.structures_for_target(uniprot, inchi)
    return [TargetStructure(**s) for s in structures]
