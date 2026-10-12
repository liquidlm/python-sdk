# liquidlm-python

Python client for the LiquidLM public API. One transport abstraction backs
synchronous and asynchronous clients; typed models are generated from the
pinned public OpenAPI contract while auth, errors, retries, pagination,
streaming and uploads stay hand-written and readable.

```python
from liquidlm import LiquidLM

with LiquidLM(token="...") as client:
    results = client.search_hybrid("deployment runbook", limit=5)
```

Async works the same way with `AsyncLiquidLM` and `await`/`async for`. The
`/search/*` endpoints use the `QUERY` method natively — no transport hacks.
Mutation requests are never retried automatically; uploads reconcile through
the attempt protocol and never send API credentials to storage URLs.

## Development

```sh
uv sync --extra dev   # locked toolchain (uv.lock)
pytest                # tests use mocked transports; no live account is needed
ruff check . && mypy src
python scripts/generate_models.py --check   # contract/model drift
```

The contract snapshot under `contract/` is checksummed; upgrade it, the
manifest and the generated models together after review. This candidate has
not been published; the PyPI name is provisional until ownership is confirmed.
See [SUPPORT.md](SUPPORT.md) and [CHANGELOG.md](CHANGELOG.md).
