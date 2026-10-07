"""Postgres-backed cache for external API calls (spec §3.3).

Graceful no-op when DATABASE_URL isn't set: every call is a live fetch, no
caching, no error -- so the app runs locally and in CI without a database.
Degrades the same way if DATABASE_URL is set but the database can't be
reached at all (pool checkout or the one-time schema statement fails) -- a
cache outage should never take the API down, just make it slower, and never
as a raw unhandled exception.

Connections are pooled, not opened fresh per call: a single request can make
many cache lookups in a row (e.g. PubChem + ChEMBL + a per-target HPA call
each for one /drugs/{rxcui} response), so pooling turns that into one
connection per burst instead of one per lookup. `min_size=0` means no
connection is held open while the app is idle.

When the database IS reachable, misses and expired entries are refetched; if
the refetch fails, a stale cached entry is served instead (marked
`stale=True`), per spec §3.3 and the "Upstream API down, cache available"
row of spec §7.
"""

import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Json
from psycopg_pool import ConnectionPool

_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_cache (
  source      TEXT NOT NULL,
  cache_key   TEXT NOT NULL,
  response    JSONB NOT NULL,
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (source, cache_key)
);
"""

_pool: ConnectionPool | None = None
_pool_url: str | None = None
_schema_ready = False


def _ttl_days() -> int:
    return int(os.environ.get("CACHE_TTL_DAYS", "30"))


def _get_pool() -> ConnectionPool | None:
    """The pool for the current DATABASE_URL, or None if it's unset or unusable."""
    global _pool, _pool_url, _schema_ready
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None

    if _pool is not None and _pool_url != url:
        _pool.close()
        _pool = None
        _schema_ready = False

    if _pool is None:
        try:
            _pool = ConnectionPool(url, min_size=0, max_size=5, timeout=5, open=True)
            _pool_url = url
        except Exception:
            return None

    return _pool


@contextmanager
def _connect():
    """Yields a ready connection, or None if the database is unset/unreachable.

    Only connection acquisition and the one-time schema check are caught
    here -- once a working connection is handed to the caller, any error the
    caller's own queries raise propagates normally.
    """
    global _schema_ready
    pool = _get_pool()
    if pool is None:
        yield None
        return

    conn_ctx = pool.connection()
    try:
        conn = conn_ctx.__enter__()
        if not _schema_ready:
            conn.execute(_SCHEMA)
            conn.commit()
            _schema_ready = True
    except Exception:
        conn_ctx.__exit__(None, None, None)
        yield None
        return

    try:
        yield conn
    finally:
        conn_ctx.__exit__(None, None, None)


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
