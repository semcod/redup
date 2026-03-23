"""Helper functions for scan operations."""

from pathlib import Path
from typing import List

import typer

from redup.core.models import DuplicationMap


def print_scan_header(path: Path, ext_list: List[str], min_lines: int, min_similarity: float) -> None:
    """Print scan operation header."""
    typer.echo(f"🔍 Scanning: {path}")
    typer.echo(f"📁 Extensions: {', '.join(ext_list)}")
    typer.echo(f"📏 Min lines: {min_lines}")
    typer.echo(f"🎯 Min similarity: {min_similarity}")
    typer.echo("")


def print_scan_summary(dup_map: DuplicationMap) -> None:
    """Print scan operation summary."""
    typer.echo(f"📊 Scanned {dup_map.stats.files_scanned} files "
               f"({dup_map.stats.total_lines} lines, "
               f"{dup_map.stats.scan_time_ms:.0f}ms)")
    typer.echo(f"Found {dup_map.total_groups} duplicate groups "
               f"({dup_map.total_fragments} fragments, "
               f"{dup_map.total_saved_lines} lines recoverable)")
    typer.echo("")


def apply_fuzzy_similarity(dup_map: DuplicationMap, threshold: float) -> DuplicationMap:
    """Apply fuzzy similarity detection."""
    from redup.cli_app.fuzzy_similarity import _apply_fuzzy_similarity
    return _apply_fuzzy_similarity(dup_map, threshold)
