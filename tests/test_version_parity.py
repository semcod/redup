"""The static package version must equal the authoritative VERSION file (GOV-VERSION-001)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_matches_version_file() -> None:
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    source = (ROOT / "src/redup/__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', source, re.M)
    assert match is not None
    assert match.group(1) == expected
