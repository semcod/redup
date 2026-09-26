"""Tests for native Rust sequence similarity integration in matcher."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from redup.core.matcher import (
    sequence_similarity,
    sequence_similarity_rust,
)
from redup.core.tokens_hasher import find_rust_hasher_binary

CARGO_MANIFEST = (
    Path(__file__).resolve().parent.parent / "packages" / "redup-fast-hash" / "Cargo.toml"
)


@pytest.fixture(scope="module")
def ensure_rust_binary() -> Path:
    """Ensure release binary of redup-fast-hash is available or built."""
    bin_path = find_rust_hasher_binary()
    if bin_path and bin_path.is_file():
        return bin_path

    cargo = shutil.which("cargo")
    if not cargo or not CARGO_MANIFEST.is_file():
        pytest.skip("cargo not installed or packages/redup-fast-hash not found")

    try:
        subprocess.run(
            [cargo, "build", "--release", "--manifest-path", str(CARGO_MANIFEST)],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.SubprocessError, OSError) as err:
        pytest.skip(f"Failed to build native Rust binary: {err}")

    bin_path = find_rust_hasher_binary()
    if not bin_path or not bin_path.is_file():
        pytest.skip("redup-fast-hash binary not available after build")

    return bin_path


def test_rust_similarity_identical(ensure_rust_binary: Path) -> None:
    code = "def calculate_price(val, tax):\n    return val * (1.0 + tax)"
    sim = sequence_similarity(code, code, prefer_rust=True)
    assert sim == 1.0


def test_rust_similarity_close_snippets(ensure_rust_binary: Path) -> None:
    a = "def process_user(user_id):\n    validate(user_id)\n    return db().find(user_id)"
    b = "def process_user(account_id):\n    validate(account_id)\n    return db().find(account_id)"

    sim_py = sequence_similarity(a, b, prefer_rust=False)
    sim_rust = sequence_similarity(a, b, prefer_rust=True)

    # Both should detect high similarity (> 0.80)
    assert sim_py > 0.80
    assert sim_rust > 0.80
    # Should agree within 1e-4
    assert abs(sim_py - sim_rust) < 1e-4


def test_rust_similarity_completely_different(ensure_rust_binary: Path) -> None:
    a = "x = 10"
    b = "class AuthenticationManager:\n    def login(self, u, p):\n        pass"
    sim = sequence_similarity(a, b, prefer_rust=True)
    assert sim < 0.3


def test_sequence_similarity_rust_missing_binary() -> None:
    res = sequence_similarity_rust("a", "b", binary_path=Path("/tmp/nonexistent_similarity_bin"))
    assert res is None
