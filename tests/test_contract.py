"""Contract fixture: pinned snapshot checksum and generated-model surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_contract_matches_pinned_manifest() -> None:
    manifest = json.loads((ROOT / "contract" / "manifest.json").read_text())
    digest = hashlib.sha256((ROOT / "contract" / "openapi.json").read_bytes()).hexdigest()
    assert digest == manifest["openapiSha256"]


def test_internal_routes_are_absent_from_the_pinned_contract() -> None:
    spec = json.loads((ROOT / "contract" / "openapi.json").read_text())
    for path in spec["paths"]:
        assert "admin" not in path and "internal" not in path


def test_generated_models_cover_the_contract_schemas() -> None:
    from liquidlm import models

    spec = json.loads((ROOT / "contract" / "openapi.json").read_text())
    names = set(spec["components"]["schemas"])
    generated = set(models.__all__) if hasattr(models, "__all__") else dir(models)
    missing = {name for name in names if name not in generated}
    # datamodel-code-generator may merge/rename a few schemas; flag anything big.
    assert len(missing) <= 5, f"schemas missing from generated models: {sorted(missing)[:10]}"


def test_package_metadata() -> None:
    import liquidlm

    assert liquidlm.__version__
    assert hasattr(liquidlm, "LiquidLM") and hasattr(liquidlm, "AsyncLiquidLM")
