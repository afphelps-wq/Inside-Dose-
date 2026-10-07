import httpx
import pytest

from backend.app.services import rcsb

# Real shape confirmed against the live RCSB search API while building this
# service: apixaban's PDB ligand id is GG2, and 2P16 ("Factor Xa in Complex
# with the Inhibitor APIXABAN") is the one structure with it bound.
APIXABAN_INCHI = "InChI=1S/C25H30ClN5O4/c1-31-23(32)17..."


@pytest.fixture(autouse=True)
def no_real_cache(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)


def _response(url, json_body, status=200):
    response = httpx.Response(status, json=json_body)
    response._request = httpx.Request("POST", url)
    return response


def test_ligand_id_for_inchi_returns_first_match(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        return _response(url, {"result_set": [{"identifier": "GG2"}]})
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    assert rcsb.ligand_id_for_inchi(APIXABAN_INCHI) == "GG2"


def test_ligand_id_for_inchi_none_when_no_match(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        return _response(url, {}, status=404)
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    assert rcsb.ligand_id_for_inchi(APIXABAN_INCHI) is None


def test_ligand_id_for_inchi_degrades_on_upstream_error(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    assert rcsb.ligand_id_for_inchi(APIXABAN_INCHI) is None


def test_structures_for_target_flags_drug_bound_structure(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        query = json["query"]
        if query.get("service") == "chemical":
            return _response(url, {"result_set": [{"identifier": "GG2"}]})
        if query.get("type") == "group":
            return _response(url, {"result_set": [{"identifier": "2P16"}]})
        # plain uniprot search -- doesn't include 2P16 in its capped top results,
        # same as the real API for factor Xa (192 total structures).
        return _response(url, {"result_set": [{"identifier": "1FAX"}, {"identifier": "1KSN"}]})
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    monkeypatch.setattr(rcsb, "entry_title", lambda pdb_id: f"Title for {pdb_id}")

    structures = rcsb.structures_for_target("P00742", APIXABAN_INCHI)
    assert structures[0] == {"pdb_id": "2P16", "title": "Title for 2P16", "has_this_drug": True}
    assert {s["pdb_id"] for s in structures} == {"2P16", "1FAX", "1KSN"}
    assert all(s["has_this_drug"] is False for s in structures[1:])


def test_structures_for_target_without_inchi_has_no_drug_bound_flags(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        return _response(url, {"result_set": [{"identifier": "1FAX"}]})
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    monkeypatch.setattr(rcsb, "entry_title", lambda pdb_id: "Factor Xa")

    structures = rcsb.structures_for_target("P00742", None)
    assert structures == [{"pdb_id": "1FAX", "title": "Factor Xa", "has_this_drug": False}]


def test_structures_for_target_empty_when_no_structures(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        return _response(url, {}, status=404)
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    assert rcsb.structures_for_target("P00742", None) == []


def test_structures_for_target_degrades_on_upstream_error(monkeypatch):
    def fake_post(self, url, json=None, timeout=None):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    assert rcsb.structures_for_target("P00742", None) == []


def test_structures_for_target_caps_at_max_structures(monkeypatch):
    many_ids = [{"identifier": f"ID{i}"} for i in range(rcsb.MAX_STRUCTURES + 5)]

    def fake_post(self, url, json=None, timeout=None):
        return _response(url, {"result_set": many_ids})
    monkeypatch.setattr(httpx.Client, "post", fake_post)
    monkeypatch.setattr(rcsb, "entry_title", lambda pdb_id: pdb_id)

    structures = rcsb.structures_for_target("P00742", None)
    assert len(structures) == rcsb.MAX_STRUCTURES


def test_entry_title_returns_struct_title(monkeypatch):
    def fake_get(self, url, timeout=None):
        response = httpx.Response(200, json={"struct": {"title": "Factor Xa in Complex with Apixaban"}})
        response._request = httpx.Request("GET", url)
        return response
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    assert rcsb.entry_title("2P16") == "Factor Xa in Complex with Apixaban"


def test_entry_title_falls_back_to_pdb_id_on_failure(monkeypatch):
    def fake_get(self, url, timeout=None):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    assert rcsb.entry_title("2P16") == "2P16"
