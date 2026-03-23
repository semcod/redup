"""Scan command implementations for reDUP CLI."""

from pathlib import Path
from typing import Any

import typer

from redup.core.config import create_sample_redup_toml
from redup.core.models import DuplicationMap
from redup.core.pipeline import analyze, analyze_parallel, analyze_optimized
from redup.cli_app.config_builder import build_config, build_config_with_file_support
from redup.cli_app.output_writer import write_output
from redup.cli_app.scan_helpers import print_scan_header, print_scan_summary, apply_fuzzy_similarity


def scan_command(
    path: Path = typer.Argument(Path("."), help="Project root directory to scan.", exists=True, dir_okay=True, file_okay=False),
    format: str = typer.Option("toon", "--format", "-f", help="Output format (json, yaml, toon, markdown, code2llm, all, enhanced)."),
    output: Any = typer.Option(None, "--output", "-o", help="Output directory or file path. Defaults to stdout."),
    extensions: Any = typer.Option(None, "--ext", "-e", help="Comma-separated file extensions to scan. Overrides config."),
    min_lines: Any = typer.Option(None, "--min-lines", help="Minimum block size (lines). Overrides config."),
    min_similarity: Any = typer.Option(None, "--min-sim", help="Minimum similarity score (0.0-1.0). Overrides config."),
    include_tests: bool = typer.Option(False, "--include-tests", help="Include test files in analysis."),
    functions_only: bool = typer.Option(False, "--functions-only", help="Only analyze function-level duplicates."),
    parallel: bool = typer.Option(False, "--parallel", help="Use parallel processing for faster analysis."),
    max_workers: Any = typer.Option(None, "--max-workers", help="Maximum number of parallel workers."),
    incremental: bool = typer.Option(False, "--incremental", help="Use incremental scanning (cache-based)."),
    memory_cache: bool = typer.Option(True, "--memory-cache/--no-memory-cache", help="Use memory cache for faster processing."),
    max_cache_mb: int = typer.Option(512, "--max-cache-mb", help="Maximum memory cache size in MB."),
    fuzzy: bool = typer.Option(False, "--fuzzy", help="Enable fuzzy similarity detection."),
    fuzzy_threshold: float = typer.Option(0.8, "--fuzzy-threshold", help="Fuzzy similarity threshold (0.0-1.0)."),
) -> None:
    """Scan a project for code duplicates."""
    
    # Build configuration
    if any([extensions, min_lines, min_similarity, include_tests, functions_only, parallel, max_workers, incremental, memory_cache, max_cache_mb, fuzzy]):
        config = build_config_with_file_support(
            path, extensions, min_lines, min_similarity, include_tests,
            parallel, max_workers, incremental, memory_cache, max_cache_mb, functions_only, fuzzy, fuzzy_threshold
        )
    else:
        config = build_config(path, extensions, min_lines, min_similarity, include_tests)
    
    # Print scan header
    print_scan_header(path, config.extensions, config.min_block_lines, config.min_similarity)
    
    # Run analysis
    if parallel and max_workers and max_workers > 1:
        dup_map = analyze_parallel(config, max_workers)
    elif memory_cache:
        dup_map = analyze_optimized(config, use_memory_cache=True, max_cache_mb=max_cache_mb)
    else:
        dup_map = analyze(config, function_level_only=functions_only)
    
    # Apply fuzzy similarity if requested
    if fuzzy:
        dup_map = apply_fuzzy_similarity(dup_map, fuzzy_threshold)
    
    # Print summary
    print_scan_summary(dup_map)
    
    # Write results
    from redup.cli_app.output_writer import write_results
    write_results(dup_map, format, output, path)


def diff_command(before: Path, after: Path) -> None:
    """Compare two reDUP analysis results."""
    from redup.core.differ import compare_scans, format_diff_result
    
    try:
        diff = compare_scans(before, after)
        result = format_diff_result(diff)
        typer.echo(result)
    except Exception as e:
        typer.echo(f"❌ Error comparing scans: {e}", err=True)
        raise typer.Exit(1)


def check_command(
    path: Path = typer.Argument(Path("."), help="Project root directory to check.", exists=True, dir_okay=True, file_okay=False),
    max_groups: int = typer.Option(10, "--max-groups", help="Maximum duplicate groups to report."),
    max_saved_lines: int = typer.Option(100, "--max-saved-lines", help="Maximum saved lines to report."),
    extensions: Any = typer.Option(None, "--ext", "-e", help="Comma-separated file extensions to scan."),
    min_lines: Any = typer.Option(None, "--min-lines", help="Minimum block size (lines)."),
    min_similarity: Any = typer.Option(None, "--min-sim", help="Minimum similarity score (0.0-1.0)."),
    include_tests: bool = typer.Option(False, "--include-tests", help="Include test files."),
) -> None:
    """Quick check for duplicates with summary report."""
    
    config = build_config_with_file_support(
        path, extensions, min_lines, min_similarity, include_tests
    )
    
    print_scan_header(path, config.extensions, config.min_block_lines, config.min_similarity)
    
    dup_map = analyze(config)
    print_scan_summary(dup_map)
    
    # Show top duplicate groups
    if dup_map.groups:
        typer.echo(f"\n🎯 Top {min(max_groups, len(dup_map.groups))} duplicate groups:")
        for i, group in enumerate(dup_map.sorted_by_impact()[:max_groups]):
            if group.saved_lines_potential <= max_saved_lines:
                break
            typer.echo(f"  {i+1}. {group.id}: {group.occurrences} occurrences, {group.saved_lines_potential} lines recoverable")
    else:
        typer.echo("✅ No duplicates found!")


def config_command(init: bool = typer.Option(False, "--init", help="Create sample redup.toml configuration."),
                   show: bool = typer.Option(False, "--show", help="Show current configuration.")) -> None:
    """Manage reDUP configuration."""
    
    if init:
        config_path = Path("redup.toml")
        if config_path.exists():
            typer.echo("⚠️  redup.toml already exists. Overwrite? [y/N]", nl=False)
            response = input().strip().lower()
            if response != 'y':
                typer.echo("Cancelled.")
                return
        
        content = create_sample_redup_toml()
        config_path.write_text(content, encoding="utf-8")
        typer.echo(f"✅ Created sample configuration: {config_path}")
    
    elif show:
        from redup.core.config import load_config
        config = load_config()
        typer.echo("Current configuration:")
        typer.echo(f"  Extensions: {config.get('extensions', ['.py'])}")
        typer.echo(f"  Min lines: {config.get('min_lines', 3)}")
        typer.echo(f"  Min similarity: {config.get('min_similarity', 0.8)}")
        typer.echo(f"  Include tests: {config.get('include_tests', False)}")
    
    else:
        typer.echo("Use --init to create config or --show to display current config.")


def info_command() -> None:
    """Show reDUP version and system information."""
    import redup
    import sys
    
    typer.echo(f"reDUP version: {redup.__version__}")
    typer.echo(f"Python version: {sys.version}")
    typer.echo(f"Installation path: {Path(redup.__file__).parent}")
    
    # Check optional dependencies
    deps = {
        "tree-sitter": "tree_sitter",
        "datasketch": "datasketch", 
        "rapidfuzz": "rapidfuzz",
    }
    
    typer.echo("\nOptional dependencies:")
    for name, module in deps.items():
        try:
            __import__(module)
            typer.echo(f"  ✅ {name}")
        except ImportError:
            typer.echo(f"  ❌ {name} (install with: pip install {name})")
