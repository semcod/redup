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
from redup.core.config import config_to_scan_config, create_sample_redup_toml, load_config  # noqa: E402
from redup.core.models import DuplicationMap, ScanConfig  # noqa: E402
from redup.core.pipeline import analyze  # noqa: E402
from redup.reporters.json_reporter import to_json  # noqa: E402
from redup.reporters.markdown_reporter import to_markdown  # noqa: E402
from redup.reporters.toon_reporter import to_toon  # noqa: E402
from redup.reporters.yaml_reporter import to_yaml  # noqa: E402

app = typer.Typer(
    name="redup",
    help="reDUP — Code duplication analyzer and refactoring planner for LLMs.",
    add_completion=False,
)


OutputFormat = Literal["json", "yaml", "toon", "all"]


DEFAULT_PATH = Path(".")
DEFAULT_FORMAT: OutputFormat = "toon"
DEFAULT_OUTPUT: Path | None = None


def _write_output(content: str, output: Path | None, suffix: str) -> None:
    """Write content to file or stdout."""
    if output:
        target = output if output.suffix else output / f"duplication.{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        typer.echo(f"  → {target}")
    else:
        typer.echo(content)


def _build_config(
    path: Path,
    extensions: str,
    min_lines: int,
    min_similarity: float,
    include_tests: bool
) -> ScanConfig:
    """Build scan configuration from CLI arguments."""
    ext_list = [e.strip() if e.startswith(".") else f".{e.strip()}" for e in extensions.split(",")]

    return ScanConfig(
        root=path,
        extensions=ext_list,
        min_block_lines=min_lines,
        min_similarity=min_similarity,
        include_tests=include_tests,
    )


def _build_config_with_file_support(
    path: Path,
    extensions: str | None,
    min_lines: int | None,
    min_similarity: float | None,
    include_tests: bool | None
) -> ScanConfig:
    """Build scan configuration supporting config files and CLI overrides."""
    # Load configuration from files
    file_config = load_config()
    
    # Use CLI arguments to override file config (if provided)
    if extensions is not None:
        file_config["extensions"] = extensions
    if min_lines is not None:
        file_config["min_lines"] = min_lines
    if min_similarity is not None:
        file_config["min_similarity"] = min_similarity
    if include_tests is not None:
        file_config["include_tests"] = include_tests
    
    return config_to_scan_config(file_config, path)


def _print_scan_header(
    path: Path,
    ext_list: list[str],
    min_lines: int,
    min_similarity: float,
) -> None:
    """Print scan configuration header."""
    typer.echo(f"reDUP v{redup.__version__} — scanning {path.resolve()}")
    typer.echo(f"  extensions: {', '.join(ext_list)}")
    typer.echo(f"  min_lines: {min_lines}, min_similarity: {min_similarity}")
    typer.echo("")


def _print_scan_summary(dup_map: DuplicationMap) -> None:
    """Print scan completion summary."""
    typer.echo(f"Scan complete: {dup_map.stats.files_scanned} files, "
               f"{dup_map.stats.total_lines} lines, "
               f"{dup_map.stats.scan_time_ms:.0f}ms")
    typer.echo(f"Found {dup_map.total_groups} duplicate groups "
               f"({dup_map.total_fragments} fragments, "
               f"{dup_map.total_saved_lines} lines recoverable)")
    typer.echo("")


def _write_results(
    dup_map: DuplicationMap,
    format: str,
    output: Path | None,
    path: Path,
) -> None:
    """Write scan results to output files."""
    output_dir = output

    if format == "all":
        if output_dir is None:
            output_dir = path / "redup_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        renderers: list[tuple[str, Callable[[DuplicationMap], str], str]] = [
            ("JSON", to_json, "json"),
            ("YAML", to_yaml, "yaml"),
            ("TOON", to_toon, "toon"),
            ("Markdown", to_markdown, "md"),
        ]
        for _fmt, renderer, suffix in renderers:
            content = renderer(dup_map)
            target = output_dir / f"duplication.{suffix}"
            target.write_text(content, encoding="utf-8")
            typer.echo(f"  → {target}")
    elif format == "json":
        _write_output(to_json(dup_map), output_dir, "json")
    elif format == "yaml":
        _write_output(to_yaml(dup_map), output_dir, "yaml")
    elif format == "toon":
        _write_output(to_toon(dup_map), output_dir, "toon")
    elif format == "markdown":
        _write_output(to_markdown(dup_map), output_dir, "md")


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
        help="Output format (json, yaml, toon, markdown, all).",
    ),
    output: Path | None = typer.Option(
        DEFAULT_OUTPUT,
        "--output", "-o",
        help="Output directory or file path. Defaults to stdout.",
    ),
    extensions: str = typer.Option(
        ".py",
        "--ext", "-e",
        help="Comma-separated file extensions to scan.",
    ),
    min_lines: int = typer.Option(
        3,
        "--min-lines",
        help="Minimum block size (lines) to consider as duplicate.",
    ),
    min_similarity: float = typer.Option(
        0.85,
        "--min-sim",
        help="Minimum similarity score (0.0-1.0) for fuzzy matches.",
    ),
    include_tests: bool = typer.Option(
        False,
        "--include-tests",
        help="Include test files in analysis.",
    ),
    functions_only: bool = typer.Option(
        False,
        "--functions-only",
        help="Only analyze function-level duplicates (faster).",
    ),
) -> None:
    """Scan a project for code duplicates and generate a refactoring map."""
    config = _build_config(path, extensions, min_lines, min_similarity, include_tests)

    _print_scan_header(path, config.extensions, min_lines, min_similarity)

    dup_map = analyze(config=config, function_level_only=functions_only)

    _print_scan_summary(dup_map)
    _write_results(dup_map, format, output, path)


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
    try:
        from redup.core.differ import compare_scans, format_diff_result
        
        diff_result = compare_scans(before, after)
        output = format_diff_result(diff_result)
        
        typer.echo(output)
        
        # Set exit code based on whether new duplicates were added
        if diff_result.new_count > 0:
            raise typer.Exit(1)
        else:
            # Don't exit - just return normally (exit code 0)
            return
            
    except Exception as e:
        typer.echo(f"Error comparing scans: {e}", err=True)
        raise typer.Exit(2)


@app.command()
def check(
    path: Path = typer.Argument(
        Path("."),
        help="Project root directory to scan.",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    max_groups: int = typer.Option(
        10,
        "--max-groups",
        help="Maximum allowed duplicate groups (default: 10).",
    ),
    max_saved_lines: int = typer.Option(
        100,
        "--max-lines",
        help="Maximum allowed recoverable lines (default: 100).",
    ),
    extensions: str = typer.Option(
        ".py",
        "--ext", "-e",
        help="Comma-separated file extensions to scan.",
    ),
    min_lines: int = typer.Option(
        3,
        "--min-lines",
        help="Minimum block size (lines) to consider as duplicate.",
    ),
    min_similarity: float = typer.Option(
        0.85,
        "--min-sim",
        help="Minimum similarity score (0.0-1.0) for fuzzy matches.",
    ),
    include_tests: bool = typer.Option(
        False,
        "--include-tests",
        help="Include test files in analysis.",
    ),
) -> None:
    """Check project for duplicates and exit with non-zero code if thresholds exceeded."""
    config = _build_config(path, extensions, min_lines, min_similarity, include_tests)
    
    dup_map = analyze(config=config, function_level_only=True)
    
    # Check thresholds
    groups_exceeded = dup_map.total_groups > max_groups
    lines_exceeded = dup_map.total_saved_lines > max_saved_lines
    
    if groups_exceeded or lines_exceeded:
        typer.echo(f"❌ reDUP check FAILED - thresholds exceeded:", err=True)
        typer.echo(f"  Duplicate groups: {dup_map.total_groups} (max: {max_groups})", err=True)
        typer.echo(f"  Recoverable lines: {dup_map.total_saved_lines} (max: {max_saved_lines})", err=True)
        
        if groups_exceeded:
            typer.echo(f"  ❌ Too many duplicate groups ({dup_map.total_groups} > {max_groups})", err=True)
        if lines_exceeded:
            typer.echo(f"  ❌ Too many duplicate lines ({dup_map.total_saved_lines} > {max_saved_lines})", err=True)
        
        raise typer.Exit(1)
    else:
        typer.echo(f"✅ reDUP check PASSED")
        typer.echo(f"  Duplicate groups: {dup_map.total_groups}/{max_groups}")
        typer.echo(f"  Recoverable lines: {dup_map.total_saved_lines}/{max_saved_lines}")
        # Don't exit - just return normally (exit code 0)
        return


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
    if init:
        config_file = Path.cwd() / "redup.toml"
        if config_file.exists():
            typer.echo(f"❌ Configuration file already exists: {config_file}")
            raise typer.Exit(1)
        
        content = create_sample_redup_toml()
        config_file.write_text(content, encoding="utf-8")
        typer.echo(f"✅ Created sample configuration: {config_file}")
        typer.echo("Edit the file to customize reDUP settings.")
        return
    
    if show:
        config = load_config()
        typer.echo("Current reDUP configuration:")
        typer.echo("=" * 40)
        
        if not config:
            typer.echo("No configuration found (using defaults)")
            return
        
        for key, value in sorted(config.items()):
            typer.echo(f"  {key}: {value}")
        return
    
    # Default: show help
    typer.echo("Use --init to create a sample configuration file.")
    typer.echo("Use --show to display current configuration.")


@app.command()
def info() -> None:
    """Show reDUP version and configuration info."""
    typer.echo(f"reDUP v{redup.__version__}")
    typer.echo("  Python package: redup")
    typer.echo("  Repo: https://github.com/semcod/redup")
    typer.echo("")
    typer.echo("Optional dependencies:")

    for name, pkg in [
        ("rapidfuzz", "rapidfuzz"),
        ("tree-sitter", "tree_sitter"),
        ("datasketch (LSH)", "datasketch"),
        ("pyyaml", "yaml"),
    ]:
        try:
            __import__(pkg)
            typer.echo(f"  ✓ {name}")
        except ImportError:
            typer.echo(f"  ✗ {name} (not installed)")


if __name__ == "__main__":
    app()
