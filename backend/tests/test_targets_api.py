import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import pubchem, rcsb, rxnorm

client = TestClient(app)

METOPROLOL_RXCUI = "6918"  # curated drug, pubchem_cid 4171 (see test_drugs_api.py)


@pytest.fixture(autouse=True)
def no_real_upstream_calls(monkeypatch):
    monkeypatch.setattr(rcsb, "structures_for_target", lambda uniprot, inchi: [])


def test_get_structures_without_rxcui(monkeypatch):
    monkeypatch.setattr(
        rcsb, "structures_for_target",
        lambda uniprot, inchi: [{"pdb_id": "1FAX", "title": "Factor Xa", "has_this_drug": False}],
    )
    response = client.get("/targets/P00742/structures")
    assert response.status_code == 200
    assert response.json() == [{"pdb_id": "1FAX", "title": "Factor Xa", "has_this_drug": False}]


def test_get_structures_resolves_rxcui_to_inchi_for_drug_bound_flag(monkeypatch):
    calls = []

    def fake_structures_for_target(uniprot, inchi):
        calls.append((uniprot, inchi))
        return [{"pdb_id": "2P16", "title": "Factor Xa w/ Apixaban", "has_this_drug": True}]

    monkeypatch.setattr(rcsb, "structures_for_target", fake_structures_for_target)
    monkeypatch.setattr(pubchem, "fetch_inchi", lambda cid: "InChI=1S/fake")

    response = client.get(f"/targets/P00742/structures?rxcui={METOPROLOL_RXCUI}")
    assert response.status_code == 200
    assert response.json()[0]["has_this_drug"] is True
    assert calls == [("P00742", "InChI=1S/fake")]


def test_get_structures_unknown_rxcui_still_returns_target_structures(monkeypatch):
    monkeypatch.setattr(rxnorm, "resolve_ingredient", lambda rxcui: None)
    monkeypatch.setattr(
        rcsb, "structures_for_target",
        lambda uniprot, inchi: [{"pdb_id": "1FAX", "title": "Factor Xa", "has_this_drug": False}],
    )
    response = client.get("/targets/P00742/structures?rxcui=0000000")
    assert response.status_code == 200
    assert response.json()[0]["pdb_id"] == "1FAX"


def test_get_structures_empty_list_when_none_found():
    response = client.get("/targets/UNKNOWN/structures")
    assert response.status_code == 200
    assert response.json() == []
