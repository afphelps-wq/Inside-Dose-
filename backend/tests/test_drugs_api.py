from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import drug_store

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


def test_get_drug_returns_curated_bundle():
    response = client.get(f"/drugs/{METOPROLOL_RXCUI}")
    assert response.status_code == 200
    body = response.json()
    assert body["rxcui"] == METOPROLOL_RXCUI
    assert body["curated"]["id"] == "metoprolol"
    assert body["molecule"] is None
    assert body["targets"] == []
    assert body["stale"] is False


def test_get_drug_unknown_rxcui_is_404():
    response = client.get("/drugs/0000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
