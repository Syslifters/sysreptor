#!/usr/bin/env python3
"""Verify all python-library API/dataclass stub pages expand successfully."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "python-library"
EXPANDER = ROOT / "scripts" / "python_autodoc.py"


def main() -> int:
    stubs = sorted(DOCS.glob("api/*.md")) + sorted(DOCS.glob("dataclasses/*.md"))
    if not stubs:
        print("No python-library API stub files found", file=sys.stderr)
        return 1

    failed = 0
    for stub in stubs:
        result = subprocess.run(
            [sys.executable, str(EXPANDER), "check", "--file", str(stub)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failed += 1
            print(result.stderr or result.stdout, file=sys.stderr)

    if failed:
        print(f"{failed} stub file(s) failed autodoc expansion", file=sys.stderr)
        return 1

    print(f"OK: {len(stubs)} python-library API pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
