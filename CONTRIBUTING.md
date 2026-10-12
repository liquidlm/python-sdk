# Contributing

Use mocked transports and synthetic fixtures; tests must not call a hosted
account. Keep the transport independent of server internals: typed models come
from the pinned public contract (`scripts/generate_models.py`), while client
ergonomics, auth, errors, retries, pagination, streaming and upload
orchestration are hand-written.

Run `pytest`, `ruff check`, `ruff format --check`, `mypy src` and
`python scripts/generate_models.py --check` before submitting. Contract changes
require a reviewed diff, a manifest checksum update and regenerated models in
the same change. Do not add automatic mutation retries or credential-bearing
storage requests.

Draft contribution policy: Developer Certificate of Origin (DCO) sign-off,
maintainer review and passing required checks, subject to maintainer acceptance
before first publication.
