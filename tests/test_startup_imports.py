"""Fresh-process regressions for the optional LSH import boundary."""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"


def run_fresh(tmp_path: Path, script: str) -> None:
    env = {**os.environ, "PYTHONPATH": str(SOURCE_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


FORBID_LSH = """
import importlib.abc
import sys
class ForbidLSH(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if (fullname == 'redup.core.lsh_matcher'
                or fullname.split('.')[0] in {'datasketch', 'scipy'}):
            raise AssertionError('Unexpected startup import: ' + fullname)
sys.meta_path.insert(0, ForbidLSH())
"""


@pytest.mark.parametrize("entry", ["sdk", "cli"])
def test_startup_does_not_import_optional_lsh(tmp_path: Path, entry: str) -> None:
    script = "import redup\nassert redup.__file__.startswith(" + repr(str(SOURCE_ROOT)) + ")\n"
    if entry == "cli":
        script += """
from typer.testing import CliRunner
from redup.cli_app.main import app
result = CliRunner().invoke(app, ['--help'])
assert result.exit_code == 0, result.output
assert 'scan' in result.output
"""
    run_fresh(tmp_path, FORBID_LSH + script)


@pytest.mark.parametrize("enabled,lines", [(False, 60), (True, 2)])
def test_ineligible_lsh_work_keeps_backend_unloaded(
    tmp_path: Path, enabled: bool, lines: int
) -> None:
    run_fresh(
        tmp_path,
        FORBID_LSH
        + f"""
from redup.core.models import ScanConfig
from redup.core.scanner_types import CodeBlock
from redup.core.pipeline.duplicate_finder import find_near_duplicate_groups
block = CodeBlock('sample.py', 1, {lines}, 'x = 1')
config = ScanConfig(lsh_enabled={enabled!r}, lsh_min_lines=50)
assert find_near_duplicate_groups([block], config) == []
assert 'redup.core.lsh_matcher' not in sys.modules
""",
    )


@pytest.mark.parametrize("module_name", ["matcher", "pipeline.duplicate_finder"])
def test_compatibility_export_keeps_native_callable(tmp_path: Path, module_name: str) -> None:
    run_fresh(
        tmp_path,
        f"""
import importlib
import inspect
import sys
module = importlib.import_module('redup.core.{module_name}')
assert 'redup.core.lsh_matcher' not in sys.modules
assert 'find_near_duplicates' in dir(module)
try:
    module.unknown_export
except AttributeError:
    pass
else:
    raise AssertionError('Unknown export must raise AttributeError')
assert 'redup.core.lsh_matcher' not in sys.modules
export = module.find_near_duplicates
from redup.core.lsh_matcher import find_near_duplicates as native
assert export is native
assert module.find_near_duplicates is export
assert inspect.signature(export) == inspect.signature(native)
if {module_name!r} == 'matcher':
    assert 'find_near_duplicates' in module.__all__
    namespace = {{}}
    exec('from redup.core.matcher import *', namespace)
    assert namespace['find_near_duplicates'] is native
""",
    )


def test_eligible_work_keeps_arguments_groups_and_patch_point(tmp_path: Path) -> None:
    run_fresh(
        tmp_path,
        """
import sys
import types
from redup.core.models import DuplicateType, ScanConfig
from redup.core.scanner_types import CodeBlock
from redup.core.pipeline import duplicate_finder
assert 'redup.core.lsh_matcher' not in sys.modules
left = CodeBlock('left.py', 1, 5, 'x = 1', function_name='sample')
right = CodeBlock('right.py', 1, 5, 'x = 2', function_name='sample')
short = CodeBlock('short.py', 1, 2, 'x = 3')
calls = []
def backend(blocks, *, threshold, min_lines):
    calls.append((blocks, threshold, min_lines))
    return {'cluster': [(left, 1.0), (right, 0.9)]}
module = types.ModuleType('redup.core.lsh_matcher')
module.find_near_duplicates = backend
sys.modules[module.__name__] = module
config = ScanConfig(lsh_min_lines=3, lsh_threshold=0.7)
groups = duplicate_finder.find_near_duplicate_groups([left, short, right], config)
assert calls == [([left, right], 0.7, 3)]
assert len(groups) == 1 and groups[0].duplicate_type == DuplicateType.NEAR_DUPLICATE
assert [fragment.file for fragment in groups[0].fragments] == ['left.py', 'right.py']
assert groups[0].normalized_hash == 'lsh_cluster'
assert abs(groups[0].similarity_score - 0.95) < 1e-12
assert duplicate_finder.find_near_duplicates is backend
duplicate_finder.find_near_duplicates = lambda *args, **kwargs: {}
assert duplicate_finder.find_near_duplicate_groups([left, right], config) == []
assert len(calls) == 1
""",
    )


def test_missing_datasketch_preserves_positive_fallback(tmp_path: Path) -> None:
    run_fresh(
        tmp_path,
        """
import importlib.abc
import sys
class MissingDatasketch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'datasketch':
            raise ModuleNotFoundError('datasketch intentionally unavailable')
sys.meta_path.insert(0, MissingDatasketch())
from redup.core.matcher import find_near_duplicates
from redup.core import lsh_matcher
from redup.core.scanner_types import CodeBlock
assert find_near_duplicates is lsh_matcher.find_near_duplicates
assert lsh_matcher.MinHash is None and lsh_matcher.MinHashLSH is None
block = CodeBlock('sample.py', 1, 4, 'def sample(value): return value * 2')
index = lsh_matcher.LSHIndex(threshold=0.8)
index.add(block)
matches = index.find_near_duplicates(block)
assert len(matches) == 1 and matches[0][0] is block
assert matches[0][1] == 1.0
assert 'scipy' not in sys.modules
""",
    )


def test_exact_duplicate_analysis_keeps_optional_backend_unloaded(tmp_path: Path) -> None:
    run_fresh(
        tmp_path,
        FORBID_LSH
        + """
from pathlib import Path
from redup import ScanConfig, analyze
from redup.core.models import DuplicateType
text = ('def sample(value):\\n    doubled = value * 2\\n'
        '    result = doubled + 1\\n    return result\\n')
Path('left.py').write_text(text)
Path('right.py').write_text(text)
report = analyze(ScanConfig(root=Path.cwd(), extensions=['.py'], min_block_lines=3,
                            functions_only=True, fuzzy_enabled=False))
assert report.stats.files_scanned == 2
assert any(group.duplicate_type == DuplicateType.EXACT and group.occurrences == 2
           for group in report.groups)
assert 'redup.core.lsh_matcher' not in sys.modules
""",
    )
