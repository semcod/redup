"""Tests for reDUP scanner."""

import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from redup.core import scanner_filters
from redup.core.models import ScanConfig
from redup.core.scanner import (
    _extract_function_blocks_python,
    _is_test_file,
    _should_exclude,
    scan_project,
)
from redup.core.scanner_cache import MemoryFileCache
from redup.core.scanner_types import ScannedFile, ScanStrategy


def test_should_exclude_git():
    assert _should_exclude(Path(".git/config"), (".git",))


def test_should_exclude_venv():
    assert _should_exclude(Path("project/venv/lib/site.py"), ("venv",))


def test_should_not_exclude_normal():
    assert not _should_exclude(Path("src/main.py"), (".git", "venv"))


def test_default_config_excludes_generated_site(tmp_path):
    from redup.core.models import ScanConfig
    from redup.core.scanner import scan_project

    (tmp_path / "source.py").write_text("def source():\n    return 1\n", encoding="utf-8")
    generated = tmp_path / "examples" / "_site"
    generated.mkdir(parents=True)
    (generated / "source.py").write_text("def source():\n    return 1\n", encoding="utf-8")

    files, stats = scan_project(ScanConfig(root=tmp_path), function_level_only=True)

    assert stats.files_scanned == 1
    assert [scanned.path for scanned in files] == ["source.py"]


def test_is_test_file():
    assert _is_test_file(Path("tests/test_foo.py"))
    assert _is_test_file(Path("src/foo_test.py"))
    assert not _is_test_file(Path("src/foo.py"))


def test_extract_function_blocks_python():
    source = """
def hello():
    print("hello")

def world():
    print("world")

class Foo:
    def bar(self):
        return 42
"""
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
        paths = {Path(f.path).name for f in files}
        assert "a.py" in paths
        assert "b.py" in paths


def test_parallel_strategy_processes_files_concurrently(tmp_path, monkeypatch):
    for name in ("a.py", "b.py"):
        (tmp_path / name).write_text("def value():\n    return 1\n", encoding="utf-8")

    worker_threads: set[int] = set()
    workers_started = threading.Barrier(2)

    def record_worker(file_path, config, preloaded_sources, file_cache, function_level_only):
        worker_threads.add(threading.get_ident())
        workers_started.wait(timeout=2)
        return ScannedFile(path=file_path.name, lines=["value = 1"], blocks=[])

    monkeypatch.setitem(scan_project.__globals__, "_process_single_file", record_worker)
    _, stats = scan_project(
        ScanConfig(root=tmp_path),
        ScanStrategy(parallel=True, max_workers=2),
        function_level_only=True,
    )

    assert stats.files_scanned == 2
    assert len(worker_threads) == 2


def test_memory_file_cache_is_safe_for_parallel_reads(tmp_path):
    source_path = tmp_path / "source.py"
    source_path.write_bytes(b"def value():\n    return 1\n")
    cache = MemoryFileCache(max_memory_mb=1)

    with ThreadPoolExecutor(max_workers=8) as executor:
        contents = list(executor.map(cache.get_file_content, [source_path] * 32))

    assert contents == [source_path.read_bytes()] * 32
    assert list(cache.cache) == [source_path]


def test_scan_project_target_files_only():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "a.py").write_text("def foo():\n    return 1\n")
        (root / "b.py").write_text("def bar():\n    return 2\n")

        config = ScanConfig(root=root, target_files=["b.py"])
        files, stats = scan_project(config)

        assert stats.files_scanned == 1
        assert stats.files_skipped == 0
        paths = {Path(f.path).name for f in files}
        assert paths == {"b.py"}


def test_scan_project_target_files_does_not_walk_tree(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "a.py").write_text("def foo():\n    return 1\n")
        (root / "b.py").write_text("def bar():\n    return 2\n")

        def fail_walk(*args, **kwargs):
            raise AssertionError("target-file scans should not walk the project tree")

        monkeypatch.setattr(scanner_filters.os, "walk", fail_walk)

        config = ScanConfig(root=root, target_files=["b.py"])
        files, stats = scan_project(config)

        assert stats.files_scanned == 1
        assert {Path(f.path).name for f in files} == {"b.py"}
