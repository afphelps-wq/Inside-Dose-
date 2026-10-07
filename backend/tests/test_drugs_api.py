from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import chembl, drug_store, pubchem, rxnorm

client = TestClient(app)

METOPROLOL_RXCUI = "6918"


def test_curated_list_includes_every_drug_file():
    response = client.get("/drugs/curated")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(drug_store.all_drugs())
    rxcuis = {entry["rxcui"] for entry in body}
    assert METOPROLOL_RXCUI in rxcuis


def test_curated_list_entry_shape():
    response = client.get("/drugs/curated")
    entry = next(e for e in response.json() if e["rxcui"] == METOPROLOL_RXCUI)
    assert entry == {
        "rxcui": METOPROLOL_RXCUI,
        "id": "metoprolol",
        "generic": "metoprolol",
        "brands": ["Lopressor"],
        "common_use": "Blood pressure / heart rate",
    }


def test_get_drug_returns_curated_bundle_with_molecule(monkeypatch):
    monkeypatch.setattr(
        pubchem, "fetch_properties",
        lambda cid: {"pubchem_cid": cid, "formula": "C15H25NO3", "weight": 267.4},
    )
    response = client.get(f"/drugs/{METOPROLOL_RXCUI}")
    assert response.status_code == 200
    body = response.json()
    assert body["rxcui"] == METOPROLOL_RXCUI
    assert body["curated"]["id"] == "metoprolol"
    assert body["molecule"] == {"pubchem_cid": 4171, "formula": "C15H25NO3", "weight": 267.4}
    assert body["targets"] == []
    assert body["stale"] is False


def test_get_drug_degrades_gracefully_when_pubchem_fails(monkeypatch):
    def boom(cid):
        raise pubchem.UpstreamError("pubchem down")

    monkeypatch.setattr(pubchem, "fetch_properties", boom)
    response = client.get(f"/drugs/{METOPROLOL_RXCUI}")
    assert response.status_code == 200
    assert response.json()["molecule"] is None


def test_get_drug_unknown_rxcui_is_404(monkeypatch):
    monkeypatch.setattr(rxnorm, "resolve_ingredient", lambda rxcui: None)
    response = client.get("/drugs/0000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_drug_live_lookup_for_uncurated_drug(monkeypatch):
    monkeypatch.setattr(
        rxnorm, "resolve_ingredient",
        lambda rxcui: {"rxcui": "999999", "generic": "sertraline", "brands": ["Zoloft"]},
    )
    monkeypatch.setattr(pubchem, "resolve_cid_by_name", lambda name: 68617)
    monkeypatch.setattr(
        pubchem, "fetch_properties",
        lambda cid: {"pubchem_cid": cid, "formula": "C17H17Cl2N", "weight": 306.2},
    )
    monkeypatch.setattr(
        chembl, "fetch_targets",
        lambda name, cid: [{"chembl_id": "CHEMBL228", "uniprot": "P31645", "gene": "SLC6A4",
                             "name": "Sodium-dependent serotonin transporter", "action": "inhibitor",
                             "plain_description": "Serotonin transporter inhibitor"}],
    )

    response = client.get("/drugs/999999")
    assert response.status_code == 200
    body = response.json()
    assert body["rxcui"] == "999999"
    assert body["generic"] == "sertraline"
    assert body["brands"] == ["Zoloft"]
    assert body["curated"] is None
    assert body["molecule"]["formula"] == "C17H17Cl2N"
    assert len(body["targets"]) == 1
    assert body["targets"][0]["gene"] == "SLC6A4"
    source_names = {s["name"] for s in body["sources"]}
    assert {"RxNorm", "PubChem", "ChEMBL"} <= source_names


def test_get_drug_live_lookup_unknown_drug_is_404(monkeypatch):
    monkeypatch.setattr(rxnorm, "resolve_ingredient", lambda rxcui: None)
    response = client.get("/drugs/9999999")
    assert response.status_code == 404


def test_get_drug_live_lookup_handles_missing_pubchem_cid(monkeypatch):
    monkeypatch.setattr(
        rxnorm, "resolve_ingredient",
        lambda rxcui: {"rxcui": "999999", "generic": "sertraline", "brands": []},
    )
    monkeypatch.setattr(pubchem, "resolve_cid_by_name", lambda name: None)
    monkeypatch.setattr(chembl, "fetch_targets", lambda name, cid: [])

    response = client.get("/drugs/999999")
    assert response.status_code == 200
    assert response.json()["molecule"] is None


def test_structure_sdf_returns_pubchem_text(monkeypatch):
    monkeypatch.setattr(pubchem, "fetch_structure_sdf", lambda cid: "fake sdf content\n$$$$\n")
    response = client.get(f"/drugs/{METOPROLOL_RXCUI}/structure.sdf")
    assert response.status_code == 200
    assert response.text == "fake sdf content\n$$$$\n"


def test_structure_sdf_upstream_failure_is_502(monkeypatch):
    def boom(cid):
        raise pubchem.UpstreamError("pubchem down")

    monkeypatch.setattr(pubchem, "fetch_structure_sdf", boom)
    response = client.get(f"/drugs/{METOPROLOL_RXCUI}/structure.sdf")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_failed"


def test_structure_sdf_unknown_rxcui_is_404(monkeypatch):
    monkeypatch.setattr(rxnorm, "resolve_ingredient", lambda rxcui: None)
    response = client.get("/drugs/0000000/structure.sdf")
    assert response.status_code == 404


def test_structure_sdf_live_lookup_for_uncurated_drug(monkeypatch):
    monkeypatch.setattr(
        rxnorm, "resolve_ingredient",
        lambda rxcui: {"rxcui": "999999", "generic": "sertraline", "brands": ["Zoloft"]},
    )
    monkeypatch.setattr(pubchem, "resolve_cid_by_name", lambda name: 68617)
    monkeypatch.setattr(pubchem, "fetch_structure_sdf", lambda cid: "sertraline sdf\n$$$$\n")

    response = client.get("/drugs/999999/structure.sdf")
    assert response.status_code == 200
    assert response.text == "sertraline sdf\n$$$$\n"


def test_structure_sdf_live_lookup_no_pubchem_cid_is_404(monkeypatch):
    monkeypatch.setattr(
        rxnorm, "resolve_ingredient",
        lambda rxcui: {"rxcui": "999999", "generic": "sertraline", "brands": []},
    )
    monkeypatch.setattr(pubchem, "resolve_cid_by_name", lambda name: None)

    response = client.get("/drugs/999999/structure.sdf")
    assert response.status_code == 404


def test_search_returns_results_with_curated_flag(monkeypatch):
    monkeypatch.setattr(
        rxnorm, "search",
        lambda q, limit=10: [
            {"rxcui": METOPROLOL_RXCUI, "generic": "metoprolol", "brand": "Lopressor"},
            {"rxcui": "999999", "generic": "sertraline", "brand": "Zoloft"},
        ],
    )
    response = client.get("/search?q=met")
    assert response.status_code == 200
    body = response.json()
    assert body == [
        {"rxcui": METOPROLOL_RXCUI, "generic": "metoprolol", "brand": "Lopressor", "curated": True},
        {"rxcui": "999999", "generic": "sertraline", "brand": "Zoloft", "curated": False},
    ]


def test_search_blank_query_returns_empty_list():
    response = client.get("/search?q=   ")
    assert response.status_code == 200
    assert response.json() == []
