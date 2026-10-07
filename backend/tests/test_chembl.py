import httpx
import pytest

from backend.app.services import chembl

# Real shapes confirmed against the live ChEMBL/UniChem APIs while building this
# service (apixaban -> CHEMBL231779 -> coagulation factor X, CHEMBL244).
MOLECULE_APIXABAN = {"molecules": [{"molecule_chembl_id": "CHEMBL231779"}]}
MOLECULE_NOT_FOUND = {"molecules": []}
MECHANISM_APIXABAN = {
    "mechanisms": [{
        "action_type": "INHIBITOR",
        "mechanism_of_action": "Coagulation factor X inhibitor",
        "molecule_chembl_id": "CHEMBL231779",
        "target_chembl_id": "CHEMBL244",
    }],
    "page_meta": {"total_count": 1},
}
TARGET_FACTOR_X = {
    "targets": [{
        "target_chembl_id": "CHEMBL244",
        "pref_name": "Coagulation factor X",
        "target_type": "SINGLE PROTEIN",
        "organism": "Homo sapiens",
        "target_components": [{
            "accession": "P00742",
            "component_type": "PROTEIN",
            "target_component_synonyms": [
                {"component_synonym": "F10", "syn_type": "GENE_SYMBOL"},
                {"component_synonym": "Factor X", "syn_type": "UNIPROT"},
            ],
        }],
    }],
}
UNICHEM_MATCH = {"compounds": [{"sources": [{"shortName": "chembl", "compoundId": "CHEMBL231779"}]}]}


@pytest.fixture(autouse=True)
def no_real_cache(monkeypatch):
    # See the matching comment in test_rxnorm.py: these tests are about the
    # service logic against mocked HTTP, not caching (test_cache.py covers that).
    monkeypatch.delenv("DATABASE_URL", raising=False)


def _mock_http(monkeypatch, get_responder=None, post_responder=None):
    def fake_get(self, url, params=None, timeout=None):
        response = get_responder(url, params)
        response._request = httpx.Request("GET", url, params=params)
        return response
    def fake_post(self, url, json=None, timeout=None):
        response = post_responder(url, json)
        response._request = httpx.Request("POST", url, json=json)
        return response
    if get_responder:
        monkeypatch.setattr(httpx.Client, "get", fake_get)
    if post_responder:
        monkeypatch.setattr(httpx.Client, "post", fake_post)


def test_fetch_targets_full_pipeline(monkeypatch):
    def get_responder(url, params):
        if "molecule.json" in url:
            return httpx.Response(200, json=MOLECULE_APIXABAN)
        if "mechanism.json" in url:
            return httpx.Response(200, json=MECHANISM_APIXABAN)
        if "target.json" in url:
            return httpx.Response(200, json=TARGET_FACTOR_X)
        raise AssertionError(f"unexpected url {url}")
    _mock_http(monkeypatch, get_responder=get_responder)

    targets = chembl.fetch_targets("apixaban", 10182969)
    assert targets == [{
        "chembl_id": "CHEMBL244",
        "uniprot": "P00742",
        "gene": "F10",
        "name": "Coagulation factor X",
        "action": "inhibitor",
        "plain_description": "Coagulation factor X inhibitor",
    }]


def test_resolve_chembl_id_falls_back_to_unichem(monkeypatch):
    def get_responder(url, params):
        if "molecule.json" in url:
            return httpx.Response(200, json=MOLECULE_NOT_FOUND)
        raise AssertionError(f"unexpected url {url}")
    def post_responder(url, body):
        assert body == {"type": "sourceID", "compound": "10182969", "sourceID": 22}
        return httpx.Response(200, json=UNICHEM_MATCH)
    _mock_http(monkeypatch, get_responder=get_responder, post_responder=post_responder)

    assert chembl.resolve_chembl_id("apixaban", 10182969) == "CHEMBL231779"


def test_resolve_chembl_id_none_without_pubchem_cid(monkeypatch):
    def get_responder(url, params):
        return httpx.Response(200, json=MOLECULE_NOT_FOUND)
    _mock_http(monkeypatch, get_responder=get_responder)

    assert chembl.resolve_chembl_id("made-up-drug", None) is None


def test_fetch_targets_empty_when_no_mechanisms(monkeypatch):
    def get_responder(url, params):
        if "molecule.json" in url:
            return httpx.Response(200, json=MOLECULE_APIXABAN)
        if "mechanism.json" in url:
            return httpx.Response(200, json={"mechanisms": []})
        raise AssertionError(f"unexpected url {url}")
    _mock_http(monkeypatch, get_responder=get_responder)

    assert chembl.fetch_targets("apixaban", 10182969) == []


def test_fetch_targets_skips_a_single_failing_target(monkeypatch):
    # Observed live: ChEMBL's target.json endpoint is flaky. One bad target
    # should not blank out the rest of the list.
    two_mechanisms = {
        "mechanisms": [
            {"action_type": "INHIBITOR", "mechanism_of_action": "A", "target_chembl_id": "CHEMBL_BAD"},
            {"action_type": "INHIBITOR", "mechanism_of_action": "B", "target_chembl_id": "CHEMBL244"},
        ]
    }

    def get_responder(url, params):
        if "molecule.json" in url:
            return httpx.Response(200, json=MOLECULE_APIXABAN)
        if "mechanism.json" in url:
            return httpx.Response(200, json=two_mechanisms)
        if "target.json" in url and params.get("target_chembl_id") == "CHEMBL_BAD":
            return httpx.Response(500, json={"error": "server error"})
        if "target.json" in url:
            return httpx.Response(200, json=TARGET_FACTOR_X)
        raise AssertionError(f"unexpected url {url}")
    _mock_http(monkeypatch, get_responder=get_responder)

    targets = chembl.fetch_targets("apixaban", 10182969)
    assert len(targets) == 1
    assert targets[0]["plain_description"] == "B"


def test_fetch_targets_preserves_mechanism_order_when_fetched_concurrently(monkeypatch):
    # Target lookups for multiple mechanisms run concurrently (perf); this
    # confirms the output still lines up with the original mechanism order
    # rather than whichever thread happens to finish first.
    target_a = {"targets": [{"target_chembl_id": "CHEMBL_A", "pref_name": "Target A", "target_components": []}]}
    target_b = {"targets": [{"target_chembl_id": "CHEMBL_B", "pref_name": "Target B", "target_components": []}]}
    two_mechanisms = {
        "mechanisms": [
            {"action_type": "INHIBITOR", "mechanism_of_action": "first", "target_chembl_id": "CHEMBL_A"},
            {"action_type": "INHIBITOR", "mechanism_of_action": "second", "target_chembl_id": "CHEMBL_B"},
        ]
    }

    def get_responder(url, params):
        if "molecule.json" in url:
            return httpx.Response(200, json=MOLECULE_APIXABAN)
        if "mechanism.json" in url:
            return httpx.Response(200, json=two_mechanisms)
        if "target.json" in url and params.get("target_chembl_id") == "CHEMBL_A":
            return httpx.Response(200, json=target_a)
        if "target.json" in url and params.get("target_chembl_id") == "CHEMBL_B":
            return httpx.Response(200, json=target_b)
        raise AssertionError(f"unexpected url {url}")
    _mock_http(monkeypatch, get_responder=get_responder)

    targets = chembl.fetch_targets("apixaban", 10182969)
    assert [t["plain_description"] for t in targets] == ["first", "second"]
