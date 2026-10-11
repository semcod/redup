"""Exercise the CLI gate with real duplicate files and configured budgets."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from redup.cli_app.config_builder import build_config_with_file_support
from redup.cli_app.main import app
from redup.core.pipeline import analyze

runner = CliRunner()


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    monkeypatch.setenv("NO_AUTOUPDATE", "1")
    for key in ("REDUP_MAX_GROUPS", "REDUP_MAX_LINES"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def duplicates(tmp_path: Path) -> Path:
    code = (
        "def calculate(value):\n"
        + "".join(f"    value += {index}\n" for index in range(12))
        + "    return value\n"
    )
    (tmp_path / "first.py").write_text(code)
    (tmp_path / "second.py").write_text(code)
    return tmp_path


def invoke(path, *options):
    return runner.invoke(app, ["check", str(path), "--ext", ".py", "--min-lines", "10", *options])


@pytest.mark.parametrize(
    "options, message",
    [
        (["--max-groups", "0", "--max-lines", "10000"], "groups"),
        (["--max-groups", "10000", "--max-lines", "0"], "recoverable lines"),
        (["--max-groups", "0", "--max-lines", "0"], "Duplicate budget exceeded"),
    ],
)
def test_actual_duplicates_fail_each_budget(duplicates, options, message):
    result = invoke(duplicates, *options)
    assert result.exit_code == 1, result.output
    assert message in result.output
    assert "Top " in result.output  # Zero budgets must not hide the diagnostics.


def test_exact_boundary_passes(duplicates):
    config = build_config_with_file_support(duplicates, ".py", 10, None, False)
    result_map = analyze(config)
    assert result_map.total_groups > 0 and result_map.total_saved_lines > 0
    result = invoke(
        duplicates,
        "--max-groups",
        str(result_map.total_groups),
        "--max-lines",
        str(result_map.total_saved_lines),
    )
    assert result.exit_code == 0, result.output
    assert "Duplicate budgets passed" in result.output


def test_zero_budget_passes_without_duplicates(tmp_path):
    (tmp_path / "unique.py").write_text("print('unique')\n")
    result = invoke(tmp_path, "--max-groups", "0", "--max-lines", "0")
    assert result.exit_code == 0, result.output
    assert "Scanned 1 files" in result.output
    assert "No duplicates found" in result.output


def test_default_budgets_pass_small_duplicate_fixture(duplicates):
    result = invoke(duplicates)
    assert result.exit_code == 0, result.output
    assert "groups <= 10, lines <= 100" in result.output


def test_default_budgets_reject_large_duplicate_fixture(duplicates):
    code = (duplicates / "first.py").read_text()
    for index in range(20):
        (duplicates / f"copy_{index}.py").write_text(code)
    result = invoke(duplicates)
    assert result.exit_code == 1, result.output
    assert "Duplicate budget exceeded" in result.output


def test_configured_budget_and_cli_override(duplicates):
    (duplicates / "redup.toml").write_text("[check]\nmax_groups = 0\nmax_lines = 0\n")
    assert invoke(duplicates).exit_code == 1
    result = invoke(duplicates, "--max-groups", "10000", "--max-lines", "10000")
    assert result.exit_code == 0, result.output


def test_environment_overrides_file_budget(duplicates, monkeypatch):
    (duplicates / "redup.toml").write_text("[check]\nmax_groups = 10000\nmax_lines = 10000\n")
    monkeypatch.setenv("REDUP_MAX_GROUPS", "0")
    assert invoke(duplicates).exit_code == 1
    assert invoke(duplicates, "--max-groups", "10000").exit_code == 0


@pytest.mark.parametrize("setting", ["max_groups = -1", "max_lines = -1", 'max_groups = "zero"'])
def test_invalid_configured_budget_is_rejected(duplicates, setting):
    (duplicates / "redup.toml").write_text("[check]\n" + setting + "\n")
    result = invoke(duplicates)
    assert result.exit_code == 2, result.output
    assert "must be a nonnegative integer" in result.output


@pytest.mark.parametrize("flag", ["--max-groups", "--max-lines"])
def test_negative_cli_budget_is_rejected(duplicates, flag):
    result = invoke(duplicates, flag, "-1")
    assert result.exit_code == 2, result.output


def test_missing_root_cannot_pass_as_zero_files(tmp_path):
    result = invoke(tmp_path / "missing", "--max-groups", "0", "--max-lines", "0")
    assert result.exit_code == 2, result.output
    assert "scan root does not exist" in result.output


def test_file_root_cannot_pass_as_zero_files(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("print('source')\n")
    result = invoke(source, "--max-groups", "0", "--max-lines", "0")
    assert result.exit_code == 2, result.output
    assert "scan root is not a directory" in result.output
