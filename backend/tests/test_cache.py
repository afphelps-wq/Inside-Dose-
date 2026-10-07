import os

import pytest

from backend.app.services.cache import cached_fetch


def test_passthrough_when_database_url_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    calls = []

    def fetch():
        calls.append(1)
        return {"value": 42}

    result, stale = cached_fetch("test", "key1", fetch)
    assert result == {"value": 42}
    assert stale is False

    # Every call is a live fetch -- no DB means no memory of the first call.
    cached_fetch("test", "key1", fetch)
    assert len(calls) == 2


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="requires a real DATABASE_URL (not set in CI)")
class TestRealDatabase:
    def test_second_call_is_a_cache_hit(self):
        calls = []

        def fetch():
            calls.append(1)
            return {"value": "first"}

        source, key = "test_real", "hit_check"
        result1, stale1 = cached_fetch(source, key, fetch)
        result2, stale2 = cached_fetch(source, key, fetch)

        assert result1 == result2 == {"value": "first"}
        assert stale1 is False and stale2 is False
        assert len(calls) == 1  # second call never invoked fetch()

    def test_stale_entry_served_when_refetch_fails(self):
        source, key = "test_real", "stale_check"
        cached_fetch(source, key, lambda: {"value": "original"})

        def failing_fetch():
            raise RuntimeError("upstream is down")

        # Force the TTL to 0 so the cached entry is treated as expired.
        os.environ["CACHE_TTL_DAYS"] = "0"
        try:
            result, stale = cached_fetch(source, key, failing_fetch)
        finally:
            del os.environ["CACHE_TTL_DAYS"]

        assert result == {"value": "original"}
        assert stale is True
