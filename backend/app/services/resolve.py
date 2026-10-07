"""Resolve an rxcui to either a curated record or a live RxNorm lookup (M6).

Shared by the drugs and targets routers -- both need to go from "rxcui the
user navigated to" to a generic name + pubchem_cid before they can call
PubChem/ChEMBL/RCSB.
"""

from backend.app.services import drug_store, pubchem, rxnorm


def resolve(rxcui: str) -> dict | None:
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
