#!/usr/bin/env python3
"""Regenerate typed models from the pinned public contract.

Fails if the contract checksum drifts from contract/manifest.json. With
--check, regenerates into a temporary file and compares bytes without writing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contract" / "openapi.json"
MANIFEST = ROOT / "contract" / "manifest.json"
OUTPUT = ROOT / "src" / "liquidlm" / "models.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    digest = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    if digest != manifest["openapiSha256"]:
        print(
            "Contract drift: contract/openapi.json no longer matches manifest.json. "
            "Review the contract diff, update the manifest and regenerate together.",
            file=sys.stderr,
        )
        return 1

    # The generator's formatter reads project config (line length) from the
    # output path's tree, so the check copy must live beside the real one.
    check_target = OUTPUT.with_suffix(".check.py")
    target = OUTPUT if not args.check else check_target
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "datamodel_code_generator",
                "--input",
                str(CONTRACT),
                "--input-file-type",
                "openapi",
                "--output",
                str(target),
                "--output-model-type",
                "pydantic_v2.BaseModel",
                "--use-annotated",
                "--use-double-quotes",
                "--snake-case-field",
                "--target-python-version",
                "3.11",
                "--formatters",
                "builtin",
                "--custom-file-header",
                "# Generated from the pinned public OpenAPI contract; do not edit.",
            ],
            check=True,
        )
        if args.check:
            if not OUTPUT.exists() or OUTPUT.read_bytes() != check_target.read_bytes():
                print(
                    "Model drift: src/liquidlm/models.py is stale; run scripts/generate_models.py",
                    file=sys.stderr,
                )
                return 1
            print(f"Models in sync with contract {digest[:12]}")
            return 0
    finally:
        check_target.unlink(missing_ok=True)
    print(f"Generated {OUTPUT} from contract {digest[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
