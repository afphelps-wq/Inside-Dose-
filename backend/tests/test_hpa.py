import httpx
import pytest

from backend.app.services import hpa

# Real shape confirmed against the live HPA search_download API while building
# this service (ADRB1 -> metoprolol's target, heart muscle protein-enriched).
ADRB1_ROW = {
    "Gene": "ADRB1",
    "Ensembl": "ENSG00000043591",
    "RNA tissue specific nTPM": {"heart muscle": "20.3", "lung": "11.4", "placenta": "27.4"},
    "Protein tissue specific Intensity": {"heart muscle": "9443.4"},
}
# A fuzzy-match decoy the real API also returns for a search=ADRB1 query --
# must be filtered out by exact Gene-field match.
HLA_DRB1_ROW = {"Gene": "HLA-DRB1", "RNA tissue specific nTPM": {"lung": "554.1"}}
F10_ROW = {  # apixaban's target: no protein data, RNA fallback
    "Gene": "F10",
    "RNA tissue specific nTPM": {"liver": "500.0"},
    "Protein tissue specific Intensity": {},
}
NOT_FOUND_ROWS = [{"Gene": "SOMETHING-ELSE", "RNA tissue specific nTPM": {}}]


@pytest.fixture(autouse=True)
def no_real_cache(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)


def _mock_get(monkeypatch, rows):
    def fake_get(self, url, params=None, timeout=None):
        response = httpx.Response(200, json=rows)
        response._request = httpx.Request("GET", url, params=params)
        return response
    monkeypatch.setattr(httpx.Client, "get", fake_get)


def test_tissue_levels_prefers_protein_over_rna(monkeypatch):
    _mock_get(monkeypatch, [ADRB1_ROW, HLA_DRB1_ROW])
    levels = hpa.tissue_levels("ADRB1")
    assert levels == {"heart muscle": {"level": "high", "basis": "protein"}}


def test_tissue_levels_falls_back_to_rna_with_no_protein_data(monkeypatch):
    _mock_get(monkeypatch, [F10_ROW])
    levels = hpa.tissue_levels("F10")
    assert levels == {"liver": {"level": "high", "basis": "rna"}}


def test_tissue_levels_filters_fuzzy_match_decoys(monkeypatch):
    # search=ADRB1 on the real API also returns HLA-DRB1; only the exact gene matters.
    _mock_get(monkeypatch, [HLA_DRB1_ROW, ADRB1_ROW])
    levels = hpa.tissue_levels("ADRB1")
    assert "heart muscle" in levels
    assert levels["heart muscle"]["basis"] == "protein"


def test_tissue_levels_empty_for_unknown_gene(monkeypatch):
    _mock_get(monkeypatch, NOT_FOUND_ROWS)
    assert hpa.tissue_levels("NOT-A-REAL-GENE") == {}


def test_tissue_levels_upstream_failure_degrades_to_empty(monkeypatch):
    def fake_get(self, url, params=None, timeout=None):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(httpx.Client, "get", fake_get)
    assert hpa.tissue_levels("ADRB1") == {}


@pytest.mark.parametrize("values,expected", [
    ({"a": 5}, {"a": "high"}),
    ({"a": 5, "b": 1}, {"a": "high", "b": "medium"}),
    ({"a": 9, "b": 5, "c": 1}, {"a": "high", "b": "medium", "c": "low"}),
    ({}, {}),
])
def test_bin_by_rank(values, expected):
    assert hpa._bin_by_rank(values) == expected
