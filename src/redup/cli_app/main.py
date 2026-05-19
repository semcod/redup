"""CLI entry point for reDUP — code duplication analyzer."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Literal

import typer

# Suppress SyntaxWarning from external libraries
warnings.filterwarnings("ignore", category=SyntaxWarning)


# Import refactored modules
from redup.cli_app.quality_commands import app as quality_app  # noqa: E402
from redup.cli_app.scan_commands import (  # noqa: E402
    check_command,
    config_command,
    diff_command,
    info_command,
    scan_command,
)

app = typer.Typer(
    name="redup",
    help="reDUP — Code duplication analyzer and refactoring planner for LLMs.",
    add_completion=False,
)
app.add_typer(quality_app, name="quality", help="Run local quality gates")


OutputFormat = Literal["json", "yaml", "toon", "markdown", "all", "enhanced", "code2llm"]


DEFAULT_PATH = Path(".")
DEFAULT_FORMAT: OutputFormat = "toon"
DEFAULT_OUTPUT: Path | None = None


@app.command()
def scan(
    path: Path = typer.Argument(DEFAULT_PATH, help="Project root directory to scan."),
    format: str = typer.Option(
        "toon",
        "--format",
        "-f",
        help="Output format (json, yaml, toon, markdown, code2llm, all, enhanced).",
    ),
    output: Path | None = typer.Option(
        DEFAULT_OUTPUT,
        "--output",
        "-o",
        help="Output directory or file path. Defaults to stdout.",
    ),
    extensions: str | None = typer.Option(
        None,
        "--ext",
        "-e",
        help="Comma-separated file extensions to scan. Overrides config.",
    ),
    min_lines: int | None = typer.Option(
        None,
        "--min-lines",
        help="Minimum block size (lines). Overrides config.",
    ),
    min_similarity: float | None = typer.Option(
        None,
        "--min-sim",
        help="Minimum similarity score (0.0-1.0). Overrides config.",
    ),
    include_tests: bool | None = typer.Option(
        None,
        "--include-tests",
        help="Include test files. Overrides config.",
    ),
    no_functions_only: bool = typer.Option(
        False,
        "--no-functions-only",
        help="Analyze all code, not just functions (default: functions-only mode is ON).",
    ),
    no_parallel: bool = typer.Option(
        False,
        "--no-parallel",
        help="Disable parallel scanning for large projects (default: disabled).",
    ),
    max_workers: int | None = typer.Option(
        None,
        "--max-workers",
        help="Maximum number of parallel workers.",
    ),
    incremental: bool = typer.Option(
        False,
        "--incremental",
        help="Use incremental scanning with caching.",
    ),
    no_memory_cache: bool = typer.Option(
        False,
        "--no-memory-cache",
        help="Disable memory cache for scanning.",
    ),
    max_cache_mb: int = typer.Option(
        512,
        "--max-cache-mb",
        help="Maximum memory cache size in MB.",
    ),
    changed_only: bool = typer.Option(
        False,
        "--changed-only",
        help="Scan only files changed relative to git base ref.",
    ),
    base_ref: str = typer.Option(
        "HEAD",
        "--base-ref",
        help="Git base ref used by --changed-only (e.g. HEAD, origin/main).",
    ),
    include_untracked: bool = typer.Option(
        True,
        "--include-untracked/--no-include-untracked",
        help="Include untracked files in --changed-only mode.",
    ),
    fuzzy: bool = typer.Option(
        False,
        "--fuzzy",
        help="Enable fuzzy similarity detection.",
    ),
    fuzzy_threshold: float = typer.Option(
        0.8,
        "--fuzzy-threshold",
        help="Fuzzy similarity threshold (0.0-1.0).",
    ),
) -> None:
    """Scan a project for code duplicates."""
    return scan_command(
        path,
        format,
        output,
        extensions,
        min_lines,
        min_similarity,
        include_tests,
        not no_functions_only,
        not no_parallel,
        max_workers,
        incremental,
        not no_memory_cache,
        max_cache_mb,
        changed_only,
        base_ref,
        include_untracked,
        fuzzy,
        fuzzy_threshold,
    )


@app.command()
def compare(
    project_a: Path = typer.Argument(..., help="Root directory of the first project."),
    project_b: Path = typer.Argument(..., help="Root directory of the second project."),
    threshold: float = typer.Option(
        0.75, "--threshold", "-t", help="Minimum similarity threshold."
    ),
    semantic: bool = typer.Option(
        False, "--semantic", help="Enable semantic similarity (slow, requires redup[semantic])."
    ),
    extensions: str | None = typer.Option(
        None, "--ext", "-e", help="Comma-separated file extensions to scan."
    ),
    min_lines: int = typer.Option(3, "--min-lines", help="Minimum block size (lines)."),
    no_community: bool = typer.Option(
        False, "--no-community", help="Skip community detection (no networkx needed)."
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Write JSON report to file."),
    refactor_plan: bool = typer.Option(
        False, "--refactor-plan", help="Generate LLM-powered refactoring TODO list."
    ),
    llm_model: str | None = typer.Option(
        None, "--llm-model", help="LLM model for refactoring plan (default: from LLM_MODEL env)."
    ),
    env_file: Path | None = typer.Option(None, "--env", help="Path to .env file with API keys."),
) -> None:
    """Compare two projects and recommend refactoring strategy (merge / extract / keep separate)."""
    from redup.cli_app.compare_command import compare_command

    return compare_command(
        project_a,
        project_b,
        threshold,
        semantic,
        extensions,
        min_lines,
        no_community,
        output,
        refactor_plan,
        llm_model,
        env_file,
    )


@app.command()
def diff(
    before: Path = typer.Argument(..., help="Path to the earlier scan JSON file."),
    after: Path = typer.Argument(..., help="Path to the later scan JSON file."),
) -> None:
    """Compare two reDUP scans and show the differences."""
    return diff_command(before, after)


@app.command()
def check(
    path: Path = typer.Argument(Path("."), help="Project root directory to scan."),
    max_groups: int | None = typer.Option(
        None,
        "--max-groups",
        help="Maximum allowed duplicate groups. Overrides config.",
    ),
    max_saved_lines: int | None = typer.Option(
        None,
        "--max-lines",
        help="Maximum allowed recoverable lines. Overrides config.",
    ),
    extensions: str | None = typer.Option(
        None,
        "--ext",
        "-e",
        help="Comma-separated file extensions to scan. Overrides config.",
    ),
    min_lines: int | None = typer.Option(
        None,
        "--min-lines",
        help="Minimum block size (lines). Overrides config.",
    ),
    min_similarity: float | None = typer.Option(
        None,
        "--min-sim",
        help="Minimum similarity score (0.0-1.0). Overrides config.",
    ),
    include_tests: bool | None = typer.Option(
        None,
        "--include-tests",
        help="Include test files. Overrides config.",
    ),
) -> None:
    """Check project for duplicates and exit with non-zero code if thresholds exceeded."""
    return check_command(
        path, max_groups, max_saved_lines, extensions, min_lines, min_similarity, include_tests
    )


@app.command()
def config(
    init: bool = typer.Option(
        False,
        "--init",
        help="Create a sample redup.toml configuration file.",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration (files + env vars).",
    ),
) -> None:
    """Manage reDUP configuration."""
    return config_command(init, show)


@app.command()
def info() -> None:
    """Show reDUP version and configuration info."""
    return info_command()


# Import and add tasks command
try:
    from redup.cli_app.tasks_command import app as tasks_app

    app.add_typer(tasks_app, name="tasks", help="Export duplications as tasks to TODO.md")
except ImportError:
    # tasks command requires optional planfile dependency
    pass


if __name__ == "__main__":
    app()
