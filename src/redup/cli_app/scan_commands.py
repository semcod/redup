"""Scan command implementations for reDUP CLI."""

import subprocess
from pathlib import Path
from typing import Any

import typer

from redup.cli_app.config_builder import build_config, build_config_with_file_support
from redup.cli_app.scan_helpers import print_scan_header, print_scan_summary
from redup.core.config import create_sample_redup_toml
from redup.core.pipeline import analyze, analyze_optimized


def _validate_scan_path(path: Path) -> Path:
    """Reject invalid roots before a zero-file report can overwrite a valid scan."""
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise typer.BadParameter(f"scan root does not exist: {resolved}", param_hint="path")
    if not resolved.is_dir():
        raise typer.BadParameter(f"scan root is not a directory: {resolved}", param_hint="path")
    return resolved


def _resolve_changed_files(
    path: Path,
    base_ref: str,
    include_untracked: bool,
) -> list[str]:
    """Resolve changed files relative to git base reference."""
    root = path.resolve()

    try:
        diff_proc = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", "--diff-filter=ACMRTUXB", base_ref, "--"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise typer.BadParameter("git is required for --changed-only mode") from exc

    if diff_proc.returncode != 0:
        error_output = diff_proc.stderr.strip() or diff_proc.stdout.strip()
        raise typer.BadParameter(
            f"failed to resolve changed files against {base_ref!r}: {error_output}"
        )

    changed: set[str] = {
        line.strip() for line in diff_proc.stdout.splitlines() if line.strip()
    }

    if include_untracked:
        untracked_proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=False,
        )
        if untracked_proc.returncode == 0:
            changed.update(line.strip() for line in untracked_proc.stdout.splitlines() if line.strip())

    result: list[str] = []
    for rel in sorted(changed):
        rel_path = Path(rel)
        abs_path = (root / rel_path).resolve()
        try:
            abs_path.relative_to(root)
        except ValueError:
            continue
        if abs_path.is_file():
            result.append(rel_path.as_posix())

    return result


def scan_command(
    path: Path = typer.Argument(
        Path("."),
        help="Project root directory to scan.",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    format: str = typer.Option(
        "toon",
        "--format",
        "-f",
        help="Output format (json, yaml, toon, markdown, code2llm, all, enhanced).",
    ),
    output: Any = typer.Option(
        None, "--output", "-o", help="Output directory or file path. Defaults to stdout."
    ),
    extensions: Any = typer.Option(
        None, "--ext", "-e", help="Comma-separated file extensions to scan. Overrides config."
    ),
    min_lines: Any = typer.Option(
        None, "--min-lines", help="Minimum block size (lines). Overrides config."
    ),
    min_similarity: Any = typer.Option(
        None, "--min-sim", help="Minimum similarity score (0.0-1.0). Overrides config."
    ),
    include_tests: bool = typer.Option(
        False, "--include-tests", help="Include test files in analysis."
    ),
    functions_only: bool = typer.Option(
        True,
        "--functions-only",
        help="Only analyze function-level duplicates (default: enabled for speed).",
    ),
    parallel: bool = typer.Option(
        False, "--parallel", help="Use parallel processing for faster analysis."
    ),
    max_workers: Any = typer.Option(
        None, "--max-workers", help="Maximum number of parallel workers."
    ),
    incremental: bool = typer.Option(
        False, "--incremental", help="Use incremental scanning (cache-based)."
    ),
    memory_cache: bool = typer.Option(
        True, "--memory-cache", help="Use memory cache for faster processing."
    ),
    max_cache_mb: int = typer.Option(
        512, "--max-cache-mb", help="Maximum memory cache size in MB."
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
    fuzzy: bool = typer.Option(False, "--fuzzy", help="Enable fuzzy similarity detection."),
    fuzzy_threshold: float = typer.Option(
        0.8, "--fuzzy-threshold", help="Fuzzy similarity threshold (0.0-1.0)."
    ),
    semantic: bool | None = typer.Option(
        None,
        "--semantic/--no-semantic",
        help="Enable embedding-based semantic detection (requires reDUP[semantic]).",
    ),
    semantic_threshold: float = typer.Option(
        0.80,
        "--semantic-threshold",
        help="Semantic similarity threshold (0.0-1.0).",
    ),
    semantic_model: str | None = typer.Option(
        None,
        "--semantic-model",
        help="Sentence Transformers model used for semantic detection.",
    ),
    intent: bool = typer.Option(
        False,
        "--intent",
        help="Enable Intract intent duplicate detection (requires reDUP[intent]).",
    ),
    intent_threshold: float = typer.Option(
        0.84,
        "--intent-threshold",
        help="Intent contract similarity threshold (0.0-1.0).",
    ),
    intent_manifest: str | None = typer.Option(
        None,
        "--intent-manifest",
        help="Optional intent.yaml / intract.yaml manifest path.",
    ),
    intent_fail_on: str | None = typer.Option(
        None,
        "--intent-fail-on",
        help="Comma-separated Intract policy fail tokens for --intent scans.",
    ),
    intent_warn_on: str | None = typer.Option(
        None,
        "--intent-warn-on",
        help="Comma-separated Intract policy warn tokens for --intent scans.",
    ),
) -> None:
    """Scan a project for code duplicates."""
    path = _validate_scan_path(path)

    target_files = None
    if changed_only:
        target_files = _resolve_changed_files(path, base_ref, include_untracked)
        typer.echo(
            f"🧩 Changed-only mode: {len(target_files)} file(s) selected from git diff vs {base_ref}"
        )

    # Build configuration
    if any(
        [
            extensions,
            min_lines,
            min_similarity,
            include_tests,
            functions_only,
            parallel,
            max_workers,
            incremental,
            memory_cache,
            max_cache_mb,
            changed_only,
            fuzzy,
            semantic,
            intent,
        ]
    ):
        config = build_config_with_file_support(
            path,
            extensions,
            min_lines,
            min_similarity,
            include_tests,
            parallel,
            max_workers,
            incremental,
            memory_cache,
            max_cache_mb,
            functions_only,
            fuzzy,
            fuzzy_threshold,
            semantic,
            semantic_threshold,
            semantic_model,
            intent,
            intent_threshold,
            intent_manifest,
            intent_fail_on,
            intent_warn_on,
            target_files,
        )
    else:
        config = build_config(path, extensions, min_lines, min_similarity, include_tests)
        if target_files is not None:
            config.target_files = target_files

    # Print scan header
    print_scan_header(path, config.extensions, config.min_block_lines, config.min_similarity)

    # Run analysis
    if parallel or memory_cache or incremental:
        dup_map = analyze_optimized(config, use_memory_cache=memory_cache, max_cache_mb=max_cache_mb)
    else:
        dup_map = analyze(config)

    # Print summary
    print_scan_summary(dup_map)

    # Write results
    from redup.cli_app.output_writer import write_results

    write_results(dup_map, format, output, path)

    if intent:
        from redup.cli_app.intract_commands import apply_scan_intent_policy

        try:
            policy = apply_scan_intent_policy(path, config, dup_map)
        except ImportError:
            typer.echo("WARN: Intract policy check skipped (install redup[intent])", err=True)
            return

        if policy.warnings:
            typer.echo("\nIntract warnings:")
            for item in policy.warnings:
                typer.echo(f"  - {item}")

        if policy.should_fail:
            typer.echo("\nIntract policy failed:", err=True)
            for item in policy.reasons:
                typer.echo(f"  - {item}", err=True)
            raise typer.Exit(1)


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
    path: Path = typer.Argument(
        Path("."),
        help="Project root directory to check.",
        exists=True,
        dir_okay=True,
        file_okay=False,
    ),
    max_groups: int = typer.Option(10, "--max-groups", help="Maximum duplicate groups to report."),
    max_saved_lines: int = typer.Option(
        100, "--max-saved-lines", help="Maximum saved lines to report."
    ),
    extensions: Any = typer.Option(
        None, "--ext", "-e", help="Comma-separated file extensions to scan."
    ),
    min_lines: Any = typer.Option(None, "--min-lines", help="Minimum block size (lines)."),
    min_similarity: Any = typer.Option(
        None, "--min-sim", help="Minimum similarity score (0.0-1.0)."
    ),
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
        _max_groups = max_groups if max_groups is not None else 10
        _max_saved = max_saved_lines if max_saved_lines is not None else 100
        typer.echo(f"\n🎯 Top {min(_max_groups, len(dup_map.groups))} duplicate groups:")
        for i, group in enumerate(dup_map.sorted_by_impact()[:_max_groups]):
            if group.saved_lines_potential <= _max_saved:
                break
            typer.echo(
                f"  {i + 1}. {group.id}: {group.occurrences} occurrences, {group.saved_lines_potential} lines recoverable"
            )
    else:
        typer.echo("✅ No duplicates found!")


def config_command(
    init: bool = typer.Option(False, "--init", help="Create sample redup.toml configuration."),
    show: bool = typer.Option(False, "--show", help="Show current configuration."),
) -> None:
    """Manage reDUP configuration."""

    if init:
        config_path = Path("redup.toml")
        if config_path.exists():
            typer.echo("⚠️  redup.toml already exists. Overwrite? [y/N]", nl=False)
            response = input().strip().lower()
            if response != "y":
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
    import sys

    import redup

    typer.echo(f"reDUP version: {redup.__version__}")
    typer.echo(f"Python version: {sys.version}")
    typer.echo(f"Installation path: {Path(redup.__file__).parent}")

    # Check optional dependencies
    deps = {
        "tree-sitter": "tree_sitter",
        "datasketch": "datasketch",
        "rapidfuzz": "rapidfuzz",
        "pyyaml": "yaml",
    }

    typer.echo("\nOptional dependencies:")
    for name, module in deps.items():
        try:
            __import__(module)
            typer.echo(f"  ✅ {name}")
        except ImportError:
            typer.echo(f"  ❌ {name} (install with: pip install {name})")
