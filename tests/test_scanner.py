"""Tests for reDUP scanner."""

import tempfile
from pathlib import Path

from redup.core.models import ScanConfig
from redup.core.scanner import (
    _extract_function_blocks_python,
    _is_test_file,
    _should_exclude,
    scan_project,
)


def test_should_exclude_git():
    assert _should_exclude(Path(".git/config"), (".git",))


def test_should_exclude_venv():
    assert _should_exclude(Path("project/venv/lib/site.py"), ("venv",))


def test_should_not_exclude_normal():
    assert not _should_exclude(Path("src/main.py"), (".git", "venv"))


def test_is_test_file():
    assert _is_test_file(Path("tests/test_foo.py"))
    assert _is_test_file(Path("src/foo_test.py"))
    assert not _is_test_file(Path("src/foo.py"))


def test_extract_function_blocks_python():
    source = '''
def hello():
    print("hello")

def world():
    print("world")

class Foo:
    def bar(self):
        return 42
'''
    blocks = _extract_function_blocks_python(source, "test.py")
    names = {b.function_name for b in blocks}
    assert "hello" in names
    assert "world" in names
    assert "bar" in names


def test_extract_function_blocks_syntax_error():
    blocks = _extract_function_blocks_python("def broken(:", "bad.py")
    assert blocks == []


def test_scan_project_real_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "a.py").write_text("def foo():\n    return 1\n")
        (root / "b.py").write_text("def bar():\n    return 2\n")
        (root / "__pycache__").mkdir()
        (root / "__pycache__" / "cache.py").write_text("x = 1\n")

        config = ScanConfig(root=root)
        files, stats = scan_project(config)

        assert stats.files_scanned == 2
        assert stats.files_skipped == 0
        paths = {f.path for f in files}
        assert "a.py" in paths
        assert "b.py" in paths
