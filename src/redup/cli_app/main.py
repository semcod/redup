"""CLI entry point for reDUP — code duplication analyzer."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

import redup
from redup.core.models import ScanConfig
from redup.core.pipeline import analyze
from redup.reporters.json_reporter import to_json
from redup.reporters.toon_reporter import to_toon
from redup.reporters.yaml_reporter import to_yaml

app = typer.Typer(
    name="redup",
    help="reDUP — Code duplication analyzer and refactoring planner for LLMs.",
    add_completion=False,
)


class OutputFormat(str, Enum):
    json = "json"
    yaml = "yaml"
    toon = "toon"
    all = "all"


def _write_output(content: str, output: Path | None, suffix: str) -> None:
    """Write content to file or stdout."""
    if output:
        target = output if output.suffix else output / f"duplication.{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        typer.echo(f"  → {target}")
    else:
        typer.echo(content)


@app.command()
def scan(
    path: Path = typer.Argument(
        Path("."),
        help="Project root directory to scan.",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.toon,
        "--format", "-f",
        help="Output format.",
    ),
    output: Optional[Path] = typer.Option(
        None,
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
    ext_list = [e.strip() if e.startswith(".") else f".{e.strip()}" for e in extensions.split(",")]

    config = ScanConfig(
        root=path,
        extensions=ext_list,
        min_block_lines=min_lines,
        min_similarity=min_similarity,
        include_tests=include_tests,
    )

    typer.echo(f"reDUP v{redup.__version__} — scanning {path.resolve()}")
    typer.echo(f"  extensions: {', '.join(ext_list)}")
    typer.echo(f"  min_lines: {min_lines}, min_similarity: {min_similarity}")
    typer.echo("")

    dup_map = analyze(config=config, function_level_only=functions_only)

    typer.echo(f"Scan complete: {dup_map.stats.files_scanned} files, "
               f"{dup_map.stats.total_lines} lines, "
               f"{dup_map.stats.scan_time_ms:.0f}ms")
    typer.echo(f"Found {dup_map.total_groups} duplicate groups "
               f"({dup_map.total_fragments} fragments, "
               f"{dup_map.total_saved_lines} lines recoverable)")
    typer.echo("")

    output_dir = output

    if format == OutputFormat.all:
        if output_dir is None:
            output_dir = path / "redup_output"
        output_dir.mkdir(parents=True, exist_ok=True)

        for fmt, renderer, suffix in [
            ("JSON", to_json, "json"),
            ("YAML", to_yaml, "yaml"),
            ("TOON", to_toon, "toon"),
        ]:
            content = renderer(dup_map)
            target = output_dir / f"duplication.{suffix}"
            target.write_text(content, encoding="utf-8")
            typer.echo(f"  → {target}")
    elif format == OutputFormat.json:
        _write_output(to_json(dup_map), output_dir, "json")
    elif format == OutputFormat.yaml:
        _write_output(to_yaml(dup_map), output_dir, "yaml")
    elif format == OutputFormat.toon:
        _write_output(to_toon(dup_map), output_dir, "toon")


@app.command()
def info() -> None:
    """Show reDUP version and configuration info."""
    typer.echo(f"reDUP v{redup.__version__}")
    typer.echo(f"  Python package: redup")
    typer.echo(f"  Repo: https://github.com/semcod/redup")
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
