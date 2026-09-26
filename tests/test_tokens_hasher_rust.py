"""Tests for native Rust acceleration integration in tokens_hasher."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from redup.core.tokens_hasher import (
    find_rust_hasher_binary,
    fuzzy_simhash,
    fuzzy_simhash_rust,
)

CARGO_MANIFEST = (
    Path(__file__).resolve().parent.parent / "packages" / "redup-fast-hash" / "Cargo.toml"
)
RUST_BIN = (
    Path(__file__).resolve().parent.parent
    / "packages"
    / "redup-fast-hash"
    / "target"
    / "release"
    / "redup-fast-hash"
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


def test_rust_binary_discovery(ensure_rust_binary: Path) -> None:
    assert ensure_rust_binary is not None
    assert ensure_rust_binary.is_file()
    assert ensure_rust_binary.name == "redup-fast-hash"


def test_rust_and_python_exact_match_sample_code(ensure_rust_binary: Path) -> None:
    samples = [
        "def add(a, b):\n    return a + b\n",
        "def multiply(x, y):\n    # Calculate product\n    return x * y\n",
        """
        /* C-style function */
        int process_values(int a, int b) {
            if (a > 100 || b <= 0) {
                printf("Error: invalid values\\n");
                return -1;
            }
            return a + b * 2;
        }
        """,
        """
        function validateOrder(orderId, customerEmail) {
            // Check order validity
            if (!orderId || customerEmail === "") {
                return false;
            }
            let fee = 15.99;
            return fee > 0;
        }
        """,
    ]

    for sample in samples:
        py_hash = fuzzy_simhash(sample, prefer_rust=False)
        rust_hash = fuzzy_simhash(sample, prefer_rust=True)
        assert py_hash == rust_hash
        assert rust_hash > 0


def test_fuzzy_simhash_rust_with_missing_binary() -> None:
    # Explicitly pass non-existent binary path to ensure graceful None return
    res = fuzzy_simhash_rust("def dummy(): pass", binary_path=Path("/tmp/nonexistent_bin_12345"))
    assert res is None
