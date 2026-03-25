"""CLI entry point for reDUP — code duplication analyzer."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Literal
from pathlib import Path

import typer

# Suppress SyntaxWarning from external libraries
warnings.filterwarnings("ignore", category=SyntaxWarning)

import redup  # noqa: E402
from redup.config import config as global_config, reload_config  # noqa: E402
from redup.core.config import create_sample_redup_toml, load_config  # noqa: E402
from redup.core.models import DuplicationMap, ScanConfig  # noqa: E402

# Import refactored modules
from redup.cli_app.config_builder import build_config, build_config_with_file_support  # noqa: E402
from redup.cli_app.output_writer import write_output, write_results  # noqa: E402
from redup.cli_app.scan_commands import (  # noqa: E402
    scan_command, diff_command, check_command, config_command, info_command
)
from redup.cli_app.scan_helpers import print_scan_header, print_scan_summary  # noqa: E402

app = typer.Typer(
    name="redup",
    help="reDUP — Code duplication analyzer and refactoring planner for LLMs.",
    add_completion=False,
)


OutputFormat = Literal["json", "yaml", "toon", "markdown", "all", "enhanced", "code2llm"]


DEFAULT_PATH = Path(".")
# Use centralized config for defaults
DEFAULT_FORMAT: OutputFormat = global_config.DEFAULT_FORMAT  # type: ignore
DEFAULT_OUTPUT: Path | None = None


@app.command()
def scan(
    path: Path = typer.Argument(
        DEFAULT_PATH,
        help="Project root directory to scan.",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    format: str = typer.Option(
        "toon",
        "--format", "-f",
        help="Output format (json, yaml, toon, markdown, code2llm, all, enhanced).",
    ),
    output: Path | None = typer.Option(
        DEFAULT_OUTPUT,
        "--output", "-o",
        help="Output directory or file path. Defaults to stdout.",
    ),
    extensions: str | None = typer.Option(
        None,
        "--ext", "-e",
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
    parallel: bool = typer.Option(
        False,
        "--parallel",
        "--no-parallel",
        help="Use parallel scanning for large projects (default: disabled due to issues).",
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
        path, format, output, extensions, min_lines, min_similarity,
        include_tests, not no_functions_only, parallel, max_workers,
        incremental, not no_memory_cache, max_cache_mb, fuzzy, fuzzy_threshold
    )


@app.command()
def diff(
    before: Path = typer.Argument(
        ...,
        help="Path to the earlier scan JSON file.",
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
    after: Path = typer.Argument(
        ...,
        help="Path to the later scan JSON file.", 
        exists=True,
        dir_okay=False,
        file_okay=True,
    ),
) -> None:
    """Compare two reDUP scans and show the differences."""
    return diff_command(before, after)


@app.command()
def check(
    path: Path = typer.Argument(
        Path("."),
        help="Project root directory to scan.",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
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
        "--ext", "-e",
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
    return check_command(path, max_groups, max_saved_lines, extensions, min_lines, min_similarity, include_tests)


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


if __name__ == "__main__":
    app()
