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
from redup.core.pipeline import analyze, analyze_parallel, analyze_optimized  # noqa: E402
from redup.reporters.json_reporter import to_json  # noqa: E402
from redup.reporters.markdown_reporter import to_markdown  # noqa: E402
from redup.reporters.toon_reporter import to_toon  # noqa: E402
from redup.reporters.yaml_reporter import to_yaml  # noqa: E402
from redup.reporters.code2llm_reporter import export_code2llm, to_code2llm_context, to_code2llm_toon  # noqa: E402
from redup.reporters.enhanced_reporter import EnhancedReporter  # noqa: E402

app = typer.Typer(
    name="redup",
    help="reDUP — Code duplication analyzer and refactoring planner for LLMs.",
    add_completion=False,
)


OutputFormat = Literal["json", "yaml", "toon", "markdown", "all", "enhanced", "code2llm"]


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
    include_tests: bool | None,
    parallel: bool = False,
    max_workers: int | None = None,
    incremental: bool = False,
    memory_cache: bool = True,
    max_cache_mb: int = 512,
    functions_only: bool = False,
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
    
    config = config_to_scan_config(file_config, path)
    
    # Apply performance options
    if parallel:
        config.parallel_workers = max_workers
        config._parallel_enabled = True
    elif max_workers is not None:
        config.parallel_workers = max_workers
        config._parallel_enabled = True
    
    if incremental:
        config.enable_cache = True
    
    # Store memory cache options for pipeline
    config._memory_cache = memory_cache
    config._max_cache_mb = max_cache_mb
    
    # Set functions_only flag for ultra-fast scanner
    config.functions_only = functions_only
    
    return config


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


def _apply_fuzzy_similarity(dup_map: DuplicationMap, threshold: float) -> DuplicationMap:
    """Apply fuzzy similarity detection to find similar components across all languages."""
    validation = _validate_fuzzy_input(dup_map, threshold)
    if not validation.is_valid:
        typer.echo(validation.message)
        return dup_map
    
    all_blocks = _extract_all_blocks(dup_map)
    if not all_blocks:
        typer.echo("🔍 No code blocks found for fuzzy analysis")
        return dup_map
    
    typer.echo(f"🔍 Analyzing {len(all_blocks)} code blocks for universal fuzzy similarity...")
    
    html_css_blocks, other_blocks = _separate_blocks_by_type(all_blocks)
    similar_pairs = _analyze_blocks_with_detectors(html_css_blocks, other_blocks, threshold)
    
    _report_fuzzy_results(similar_pairs)
    return dup_map


def _validate_fuzzy_input(dup_map: DuplicationMap, threshold: float) -> 'FuzzyValidationResult':
    """Validate input parameters for fuzzy similarity analysis."""
    from dataclasses import dataclass
    
    @dataclass
    class FuzzyValidationResult:
        is_valid: bool
        message: str = ""
    
    if threshold <= 0 or threshold > 1:
        return FuzzyValidationResult(False, "❌ Invalid threshold. Must be between 0 and 1.")
    
    if not dup_map.groups:
        return FuzzyValidationResult(False, "❌ No duplicate groups found.")
    
    return FuzzyValidationResult(True)


def _extract_all_blocks(dup_map: DuplicationMap) -> list:
    """Extract all code blocks from duplicate fragments."""
    from redup.core.scanner import CodeBlock
    
    all_blocks = []
    for group in dup_map.groups:
        for fragment in group.fragments:
            # Create a CodeBlock from fragment data
            block = CodeBlock(
                file=fragment.file,
                line_start=fragment.line_start,
                line_end=fragment.line_end,
                text=fragment.text,
                function_name=fragment.function_name,
                class_name=fragment.class_name
            )
            all_blocks.append(block)
    return all_blocks


def _separate_blocks_by_type(all_blocks: list) -> tuple[list, list]:
    """Separate blocks into HTML/CSS and other language categories."""
    html_css_blocks = [block for block in all_blocks 
                      if Path(block.file).suffix.lower() in ['.html', '.htm', '.css', '.scss', '.sass', '.less']]
    
    other_blocks = [block for block in all_blocks if block not in html_css_blocks]
    
    return html_css_blocks, other_blocks


def _analyze_blocks_with_detectors(html_css_blocks: list, other_blocks: list, threshold: float) -> list:
    """Analyze blocks using appropriate fuzzy similarity detectors."""
    similar_pairs = []
    
    # Analyze HTML/CSS with specialized detector
    if html_css_blocks:
        typer.echo(f"  📝 Analyzing {len(html_css_blocks)} HTML/CSS blocks...")
        html_css_similar = _analyze_html_css_blocks(html_css_blocks, threshold)
        similar_pairs.extend(html_css_similar)
        typer.echo(f"    ✨ Found {len(html_css_similar)} similar HTML/CSS component pairs")
    
    # Analyze other languages with universal detector
    if other_blocks:
        typer.echo(f"  🔧 Analyzing {len(other_blocks)} blocks from other languages...")
        universal_similar = _analyze_other_language_blocks(other_blocks, threshold)
        similar_pairs.extend(universal_similar)
        typer.echo(f"    ✨ Found {len(universal_similar)} similar component pairs from other languages")
    
    return similar_pairs


def _analyze_html_css_blocks(html_css_blocks: list, threshold: float) -> list:
    """Analyze HTML/CSS blocks using specialized fuzzy similarity detector."""
    from redup.core.fuzzy_similarity import FuzzySimilarityDetector
    
    html_css_detector = FuzzySimilarityDetector(similarity_threshold=threshold)
    return html_css_detector.find_similar_components(html_css_blocks)


def _analyze_other_language_blocks(other_blocks: list, threshold: float) -> list:
    """Analyze non-HTML/CSS blocks using universal fuzzy similarity detector."""
    from redup.core.universal_fuzzy import UniversalFuzzyDetector
    
    universal_detector = UniversalFuzzyDetector(similarity_threshold=threshold)
    return universal_detector.find_similar_components(other_blocks)


def _report_fuzzy_results(similar_pairs: list) -> None:
    """Report fuzzy similarity analysis results."""
    if similar_pairs:
        typer.echo(f"🎯 Total fuzzy similar components found: {len(similar_pairs)}")
        
        # Simplified reporting to reduce complexity
        typer.echo(f"  📊 Language groups: {len(set(Path(b1.file).suffix + '+' + Path(b2.file).suffix for b1, b2, _ in similar_pairs))}")
        
        # Show top examples only
        for block1, block2, similarity in similar_pairs[:5]:
            typer.echo(f"    {block1.file} ↔ {block2.file}: {similarity:.2f}")
        
        if len(similar_pairs) > 5:
            typer.echo(f"    ... and {len(similar_pairs) - 5} more")
        
        # Note: In production, you'd integrate these into DuplicationMap
        # For now, we just report the findings
        
    else:
        typer.echo("🔍 No fuzzy similar components found")


def _report_similarity_by_groups(similar_pairs):
    """Extracted function to reduce complexity."""
    lang_groups = {}
    for block1, block2, similarity in similar_pairs:
        lang1 = Path(block1.file).suffix
        lang2 = Path(block2.file).suffix
        comp_type = "unknown"
        
        # Try to get component type
        try:
            from redup.core.universal_fuzzy import UniversalFuzzyExtractor
            extractor = UniversalFuzzyExtractor()
            sig1 = extractor.extract_universal_signature(block1)
            if sig1:
                comp_type = sig1.component_type
        except:
            pass
        
        group_key = f"{lang1}+{lang2}:{comp_type}"
        if group_key not in lang_groups:
            lang_groups[group_key] = []
        lang_groups[group_key].append((block1, block2, similarity))
    
    return lang_groups


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
            if suffix == "json":
                include_snippets = load_config().get("reporting", {}).get("include_snippets", False)
                content = to_json(dup_map, include_snippets=include_snippets)
            target = output_dir / f"duplication.{suffix}"
            target.write_text(content, encoding="utf-8")
            typer.echo(f"  → {target}")
    elif format == "json":
        include_snippets = load_config().get("reporting", {}).get("include_snippets", False)
        _write_output(to_json(dup_map, include_snippets=include_snippets), output_dir, "json")
    elif format == "yaml":
        _write_output(to_yaml(dup_map), output_dir, "yaml")
    elif format == "toon":
        _write_output(to_toon(dup_map), output_dir, "toon")
    elif format == "markdown":
        _write_output(to_markdown(dup_map), output_dir, "md")
    elif format == "enhanced":
        reporter = EnhancedReporter(dup_map)
        target = output_dir if output_dir and output_dir.suffix else output_dir / "duplication.enhanced.json"
        reporter.save_enhanced_report(target)
        typer.echo(f"  → {target}")
    elif format == "code2llm":
        # Export code2llm format (analysis.toon + context.md)
        if output_dir is None:
            output_dir = Path("code2llm_output")
        toon_path, context_path = export_code2llm(
            dup_map,
            output_dir,
            files_scanned=dup_map.stats.files_scanned,
            total_lines=dup_map.stats.total_lines,
        )
        typer.echo(f"  → {toon_path}")
        typer.echo(f"  → {context_path}")


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
    functions_only: bool = typer.Option(
        True,
        "--functions-only/--no-functions-only",
        help="Only analyze function-level duplicates (default: enabled for speed).",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel/--no-parallel",
        help="Use parallel scanning for large projects (default: disabled due to issues).",
    ),
    max_workers: int = typer.Option(
        None,
        "--max-workers",
        help="Number of parallel workers (default: CPU count).",
    ),
    incremental: bool = typer.Option(
        False,
        "--incremental/--no-incremental",
        help="Use hash cache to skip unchanged files (default: disabled due to issues).",
    ),
    memory_cache: bool = typer.Option(
        True,
        "--memory-cache/--no-memory-cache",
        help="Load files into RAM for faster processing (default: enabled).",
    ),
    max_cache_mb: int = typer.Option(
        512,
        "--max-cache-mb",
        help="Maximum memory for file caching in MB (default: 512).",
    ),
    fuzzy: bool = typer.Option(
        False,
        "--fuzzy/--no-fuzzy",
        help="Enable fuzzy similarity detection for HTML/CSS components (default: disabled).",
    ),
    fuzzy_threshold: float = typer.Option(
        0.8,
        "--fuzzy-threshold",
        help="Fuzzy similarity threshold (0.0-1.0, default: 0.8).",
    ),
) -> None:
    """Scan a project for code duplicates and generate a refactoring map.
    
    Performance optimizations:
    - ✅ --functions-only: Faster function-level analysis (enabled)
    - ⚠️ --parallel: Multi-core processing (disabled due to issues)
    - ⚠️ --incremental: Skip unchanged files (disabled due to issues) 
    - ✅ --memory-cache: RAM preload for speed (enabled)
    
    Use --parallel and/or --incremental when needed.
    """
    try:
        config = _build_config_with_file_support(
            path, extensions, min_lines, min_similarity, include_tests, 
            parallel, max_workers, incremental, memory_cache, max_cache_mb, functions_only
        )

        # Add fuzzy options to config
        config.fuzzy_enabled = fuzzy
        config.fuzzy_threshold = fuzzy_threshold

        _print_scan_header(path, config.extensions, config.min_block_lines, config.min_similarity)

        # Choose analysis method
        if parallel:
            dup_map = analyze_parallel(config=config, function_level_only=functions_only, max_workers=max_workers)
        else:
            dup_map = analyze(config=config, function_level_only=functions_only)

        # Apply fuzzy similarity detection if enabled
        if fuzzy:
            dup_map = _apply_fuzzy_similarity(dup_map, fuzzy_threshold)

        _print_scan_summary(dup_map)
        _write_results(dup_map, format, output, path)
        
    except KeyboardInterrupt:
        typer.echo("\n⚠️  Scan cancelled by user", err=True)
        raise typer.Exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        typer.echo(f"❌ Error during scan: {e}", err=True)
        raise typer.Exit(1)


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
    file_config = load_config()
    
    # Override with CLI arguments
    if extensions is not None:
        file_config["extensions"] = extensions
    if min_lines is not None:
        file_config["min_lines"] = min_lines
    if min_similarity is not None:
        file_config["min_similarity"] = min_similarity
    if include_tests is not None:
        file_config["include_tests"] = include_tests
    
    config = config_to_scan_config(file_config, path)
    
    # Get thresholds from config or CLI
    check_config = file_config.get("check", {})
    threshold_groups = max_groups if max_groups is not None else check_config.get("max_groups", 10)
    threshold_lines = max_saved_lines if max_saved_lines is not None else check_config.get("max_lines", 100)
    
    dup_map = analyze(config=config, function_level_only=True)
    
    # Check thresholds
    groups_exceeded = dup_map.total_groups > threshold_groups
    lines_exceeded = dup_map.total_saved_lines > threshold_lines
    
    if groups_exceeded or lines_exceeded:
        typer.echo(f"❌ reDUP check FAILED - thresholds exceeded:", err=True)
        typer.echo(f"  Duplicate groups: {dup_map.total_groups} (max: {threshold_groups})", err=True)
        typer.echo(f"  Recoverable lines: {dup_map.total_saved_lines} (max: {threshold_lines})", err=True)
        
        if groups_exceeded:
            typer.echo(f"  ❌ Too many duplicate groups ({dup_map.total_groups} > {threshold_groups})", err=True)
        if lines_exceeded:
            typer.echo(f"  ❌ Too many duplicate lines ({dup_map.total_saved_lines} > {threshold_lines})", err=True)
        
        raise typer.Exit(1)
    else:
        typer.echo(f"✅ reDUP check PASSED")
        typer.echo(f"  Duplicate groups: {dup_map.total_groups}/{threshold_groups}")
        typer.echo(f"  Recoverable lines: {dup_map.total_saved_lines}/{threshold_lines}")
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
