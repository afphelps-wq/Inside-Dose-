from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

BUPROPION = "42347"
METOPROLOL = "6918"
FLUOXETINE = "4493"
OMEPRAZOLE = "7646"
ESCITALOPRAM = "321988"
APIXABAN = "1364430"
IBUPROFEN = "5640"
UNKNOWN = "0000000"


def _post(rxcuis):
    return client.post("/interactions", json={"rxcuis": rxcuis})


def test_bupropion_metoprolol_cyp2d6_major():
    body = _post([BUPROPION, METOPROLOL]).json()
    assert body["unchecked"] == []
    [finding] = body["findings"]
    assert finding["type"] == "enzyme"
    assert finding["severity"] == "major"
    assert finding["drugs"] == [BUPROPION, METOPROLOL]
    assert "CYP2D6" in finding["mechanism"]


def test_omeprazole_escitalopram_cyp2c19_minor():
    body = _post([OMEPRAZOLE, ESCITALOPRAM]).json()
    assert body["unchecked"] == []
    [finding] = body["findings"]
    assert finding["type"] == "enzyme"
    assert finding["severity"] == "minor"
    assert finding["drugs"] == [OMEPRAZOLE, ESCITALOPRAM]
    assert "CYP2C19" in finding["mechanism"]


def test_apixaban_ibuprofen_bleeding_risk_major():
    body = _post([APIXABAN, IBUPROFEN]).json()
    assert body["unchecked"] == []
    [finding] = body["findings"]
    assert finding["type"] == "effect"
    assert finding["severity"] == "major"


def test_apixaban_ssri_bleeding_risk_major():
    body = _post([APIXABAN, FLUOXETINE]).json()
    severities = {f["severity"] for f in body["findings"]}
    assert "major" in severities


def test_findings_sorted_by_severity():
    body = _post([BUPROPION, METOPROLOL, OMEPRAZOLE, ESCITALOPRAM]).json()
    severities = [f["severity"] for f in body["findings"]]
    order = {"major": 0, "moderate": 1, "minor": 2}
    assert severities == sorted(severities, key=order.get)


def test_unknown_drug_is_unchecked():
    body = _post([METOPROLOL, UNKNOWN]).json()
    assert body["unchecked"] == [UNKNOWN]
    assert body["findings"] == []


def test_too_few_rxcuis_is_422():
    assert _post([METOPROLOL]).status_code == 422


def test_too_many_rxcuis_is_422():
    assert _post([BUPROPION, METOPROLOL, OMEPRAZOLE, ESCITALOPRAM, APIXABAN, IBUPROFEN]).status_code == 422
