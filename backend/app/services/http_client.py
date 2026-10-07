"""A shared, connection-pooled httpx.Client for every external API call.

The module-level `httpx.get`/`httpx.post` shortcuts each open and close their
own connection -- fine for a one-off script, wasteful here, where a single
/drugs/{rxcui} request can make PubChem, ChEMBL, and several HPA calls in a
row, often to the same host. A shared client keeps those connections (and
their TLS handshakes) alive between calls via HTTP keep-alive.

httpx.Client is thread-safe for concurrent use, which also lets callers
parallelize independent lookups (e.g. chembl.py's per-mechanism target
fetches) through the same client without each one paying for its own
connection.
"""

import httpx

_client: httpx.Client | None = None


def get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(limits=httpx.Limits(max_keepalive_connections=20, max_connections=20))
    return _client
