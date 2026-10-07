"""Postgres-backed cache for external API calls (spec §3.3).

Graceful no-op when DATABASE_URL isn't set: every call is a live fetch, no
caching, no error -- so the app runs locally and in CI without a database.
When DATABASE_URL is set, misses and expired entries are refetched; if the
refetch fails, a stale cached entry is served instead (marked `stale=True`),
per spec §3.3 and the "Upstream API down, cache available" row of spec §7.
"""

import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Json

_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_cache (
  source      TEXT NOT NULL,
  cache_key   TEXT NOT NULL,
  response    JSONB NOT NULL,
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (source, cache_key)
);
"""

_schema_ready = False


def _ttl_days() -> int:
    return int(os.environ.get("CACHE_TTL_DAYS", "30"))


@contextmanager
def _connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        yield None
        return
    global _schema_ready
    with psycopg.connect(url) as conn:
        if not _schema_ready:
            conn.execute(_SCHEMA)
            conn.commit()
            _schema_ready = True
        yield conn


def cached_fetch(source: str, cache_key: str, fetch):
    """fetch() is called on a cache miss or an expired entry. Returns (response, stale)."""
    with _connect() as conn:
        if conn is None:
            return fetch(), False

        row = conn.execute(
            "SELECT response, fetched_at FROM api_cache WHERE source = %s AND cache_key = %s",
            (source, cache_key),
        ).fetchone()

        if row is not None:
            response, fetched_at = row
            if datetime.now(timezone.utc) - fetched_at < timedelta(days=_ttl_days()):
                return response, False

        try:
            fresh = fetch()
        except Exception:
            if row is not None:
                return row[0], True
            raise

        conn.execute(
            """INSERT INTO api_cache (source, cache_key, response, fetched_at)
               VALUES (%s, %s, %s, now())
               ON CONFLICT (source, cache_key)
               DO UPDATE SET response = EXCLUDED.response, fetched_at = EXCLUDED.fetched_at""",
            (source, cache_key, Json(fresh)),
        )
        conn.commit()
        return fresh, False
