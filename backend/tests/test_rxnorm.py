import httpx
import pytest

from backend.app.services import rxnorm


@pytest.fixture(autouse=True)
def no_real_cache(monkeypatch):
    # These are unit tests of the service logic against mocked HTTP responses,
    # independent of caching (that's covered in test_cache.py). If the dev shell
    # happens to export a real DATABASE_URL, cached_fetch would key on the same
    # query string across tests and return a previous test's stale mock data.
    monkeypatch.delenv("DATABASE_URL", raising=False)

# Real shapes confirmed against the live RxNorm API while building this service.
APPROXIMATE_ZOLOFT = {
    "approximateGroup": {
        "candidate": [
            {"rxcui": "82728", "rxaui": "673934", "score": "7.9", "rank": "1", "name": "Zoloft", "source": "RXNORM"},
            {"rxcui": "368413", "rxaui": "12317782", "score": "7.7", "rank": "5",
             "name": "sertraline Oral Tablet [Zoloft]", "source": "RXNORM"},
        ]
    }
}
ALLRELATED_ZOLOFT = {
    "allRelatedGroup": {
        "conceptGroup": [
            {"tty": "BN", "conceptProperties": [{"rxcui": "36437", "name": "Zoloft"}]},
            {"tty": "IN", "conceptProperties": [{"rxcui": "36437", "name": "sertraline"}]},
            {"tty": "SBD", "conceptProperties": [
                {"rxcui": "202439", "name": "sertraline 50 MG Oral Tablet [Zoloft]"},
            ]},
        ]
    }
}
ALLRELATED_NO_INGREDIENT = {"allRelatedGroup": {"conceptGroup": [{"tty": "DF", "conceptProperties": []}]}}
PROPERTIES_INGREDIENT = {"properties": {"rxcui": "36437", "name": "sertraline", "tty": "IN"}}


def _mock_get(monkeypatch, responder):
    def fake_get(self, url, params=None, timeout=None):
        response = responder(url, params)
        response._request = httpx.Request("GET", url, params=params)
        return response
    monkeypatch.setattr(httpx.Client, "get", fake_get)


def test_search_dedupes_to_ingredient_level(monkeypatch):
    def responder(url, params):
        if "approximateTerm" in url:
            return httpx.Response(200, json=APPROXIMATE_ZOLOFT)
        if "allrelated" in url:
            return httpx.Response(200, json=ALLRELATED_ZOLOFT)
        raise AssertionError(f"unexpected url {url}")
    _mock_get(monkeypatch, responder)

    results = rxnorm.search("zolo")
    assert results == [{"rxcui": "36437", "generic": "sertraline", "brand": "Zoloft"}]


def test_search_skips_candidates_with_no_ingredient(monkeypatch):
    def responder(url, params):
        if "approximateTerm" in url:
            return httpx.Response(200, json=APPROXIMATE_ZOLOFT)
        if "allrelated" in url:
            return httpx.Response(200, json=ALLRELATED_NO_INGREDIENT)
        raise AssertionError(f"unexpected url {url}")
    _mock_get(monkeypatch, responder)

    assert rxnorm.search("zolo") == []


def test_resolve_ingredient_from_brand_rxcui(monkeypatch):
    def responder(url, params):
        assert "allrelated" in url
        return httpx.Response(200, json=ALLRELATED_ZOLOFT)
    _mock_get(monkeypatch, responder)

    resolved = rxnorm.resolve_ingredient("82728")
    assert resolved == {"rxcui": "36437", "generic": "sertraline", "brands": ["Zoloft"]}


def test_resolve_ingredient_already_an_ingredient(monkeypatch):
    def responder(url, params):
        if "allrelated" in url:
            return httpx.Response(200, json=ALLRELATED_NO_INGREDIENT)
        if "properties" in url:
            return httpx.Response(200, json=PROPERTIES_INGREDIENT)
        raise AssertionError(f"unexpected url {url}")
    _mock_get(monkeypatch, responder)

    resolved = rxnorm.resolve_ingredient("36437")
    assert resolved == {"rxcui": "36437", "generic": "sertraline", "brands": []}


def test_resolve_ingredient_returns_none_for_unknown_rxcui(monkeypatch):
    def responder(url, params):
        if "allrelated" in url:
            return httpx.Response(200, json=ALLRELATED_NO_INGREDIENT)
        if "properties" in url:
            return httpx.Response(200, json={})
        raise AssertionError(f"unexpected url {url}")
    _mock_get(monkeypatch, responder)

    assert rxnorm.resolve_ingredient("0000000") is None


def test_search_handles_upstream_failure_per_candidate(monkeypatch):
    def responder(url, params):
        if "approximateTerm" in url:
            return httpx.Response(200, json=APPROXIMATE_ZOLOFT)
        if "allrelated" in url:
            return httpx.Response(500, json={"error": "server error"})
        raise AssertionError(f"unexpected url {url}")
    _mock_get(monkeypatch, responder)

    assert rxnorm.search("zolo") == []
