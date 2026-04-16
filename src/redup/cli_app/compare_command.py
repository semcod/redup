"""Implementation of the ``redup compare`` CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from redup.core.comparator import CrossProjectComparison
    from redup.core.community import CodeCommunity

console = Console()


def compare_command(
    project_a: Path,
    project_b: Path,
    threshold: float,
    semantic: bool,
    extensions: str | None,
    min_lines: int,
    no_community: bool,
    output: Path | None,
    refactor_plan: bool = False,
    llm_model: str | None = None,
    env_file: Path | None = None,
) -> None:
    """Compare two projects and recommend refactoring strategy."""
    from redup.core.comparator import compare_projects

    ext_list = _parse_extensions(extensions)

    console.print(
        f"[bold]Comparing[/bold] {project_a.name} ↔ {project_b.name}  "
        f"(threshold={threshold})"
    )

    comparison = compare_projects(
        project_a,
        project_b,
        similarity_threshold=threshold,
        use_semantic=semantic,
        extensions=ext_list,
        min_lines=min_lines,
    )

    _print_summary_table(comparison)
    communities = _detect_communities(comparison, threshold, no_community)
    _print_recommendation(comparison, communities)
    _print_match_details(comparison)

    report = _build_json_report(comparison, communities)
    plan = _generate_llm_plan(report, refactor_plan, env_file, llm_model, comparison)

    _export_json(report, output)


def _parse_extensions(extensions: str | None) -> list[str] | None:
    """Parse comma-separated extensions string into list."""
    if not extensions:
        return None
    return [e.strip() for e in extensions.split(",")]


def _print_summary_table(comparison: "CrossProjectComparison") -> None:
    """Print summary statistics table."""
    table = Table(title="Cross-Project Comparison")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Project A files", str(comparison.stats_a.get("files", 0)))
    table.add_row("Project B files", str(comparison.stats_b.get("files", 0)))
    table.add_row("Project A lines", str(comparison.stats_a.get("lines", 0)))
    table.add_row("Project B lines", str(comparison.stats_b.get("lines", 0)))
    table.add_row("Cross matches", str(comparison.total_matches))
    table.add_row("Shared LOC (potential)", str(comparison.shared_loc_potential))
    console.print(table)


def _detect_communities(
    comparison: "CrossProjectComparison",
    threshold: float,
    no_community: bool,
) -> list:
    """Detect code communities if enabled and matches exist."""
    if no_community or comparison.total_matches == 0:
        return []

    try:
        from redup.core.community import detect_communities
        return detect_communities(comparison, min_similarity=threshold)
    except ImportError:
        console.print(
            "[yellow]networkx not installed — skipping community detection. "
            "Install with: pip install redup[compare][/yellow]"
        )
        return []


def _print_recommendation(
    comparison: "CrossProjectComparison",
    communities: list,
) -> None:
    """Print decision recommendation and communities table."""
    if not communities and comparison.total_matches == 0:
        console.print("\n[green]No cross-project duplicates found.[/green]")
        return

    from redup.core.decision import recommend
    rec = recommend(comparison, communities)

    console.print()
    console.print(f"[bold green]Recommendation:[/bold green] {rec.decision.value}")
    console.print(f"[dim]{rec.rationale}[/dim]")
    console.print(f"[dim]Confidence: {rec.confidence:.0%}[/dim]")

    if communities:
        _print_communities_table(communities)


def _print_communities_table(communities: list) -> None:
    """Print communities table."""
    table = Table(title="Top Communities (shared code candidates)")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Similarity", justify="right")
    table.add_column("LOC", justify="right")
    table.add_column("Members", justify="right")
    for c in communities[:10]:
        table.add_row(
            str(c.id),
            c.extraction_candidate_name,
            f"{c.avg_similarity:.2f}",
            str(c.total_loc),
            str(len(c.members)),
        )
    console.print(table)


def _print_match_details(comparison: "CrossProjectComparison") -> None:
    """Print match details table."""
    if not comparison.matches:
        return

    console.print()
    match_table = Table(title=f"Matches (top 20 of {comparison.total_matches})")
    match_table.add_column("Type")
    match_table.add_column("Similarity", justify="right")
    match_table.add_column("Function A")
    match_table.add_column("Function B")
    match_table.add_column("File A")
    match_table.add_column("File B")

    sorted_matches = sorted(comparison.matches, key=lambda m: m.similarity, reverse=True)
    for m in sorted_matches[:20]:
        match_table.add_row(
            m.similarity_type,
            f"{m.similarity:.2f}",
            m.function_a or "(block)",
            m.function_b or "(block)",
            _short_path(m.file_a),
            _short_path(m.file_b),
        )
    console.print(match_table)


def _generate_llm_plan(
    report: dict,
    refactor_plan: bool,
    env_file: Path | None,
    llm_model: str | None,
    comparison: "CrossProjectComparison",
) -> object | None:
    """Generate LLM refactoring plan if requested."""
    if not refactor_plan or comparison.total_matches == 0:
        return None

    try:
        from redup.core.refactor_advisor import (
            generate_refactor_plan,
            format_plan_markdown,
            format_plan_json,
        )

        console.print("\n[bold]Generating LLM refactoring plan...[/bold]")
        plan = generate_refactor_plan(
            report, env_path=env_file, model=llm_model,
        )

        console.print(
            f"[dim]Model: {plan.model} | "
            f"{plan.prompt_tokens}→{plan.completion_tokens} tokens | "
            f"{plan.duration_ms:.0f}ms[/dim]\n"
        )
        console.print(format_plan_markdown(plan))

        # Add plan to report
        report["refactor_plan"] = format_plan_json(plan)
        return plan

    except ImportError as e:
        console.print(f"[yellow]{e}[/yellow]")
        return None
    except RuntimeError as e:
        console.print(f"[red]LLM error: {e}[/red]")
        return None


def _export_json(report: dict, output: Path | None) -> None:
    """Export report to JSON file if path provided."""
    if not output:
        return

    output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    console.print(f"\n[bold]Report saved to:[/bold] {output}")


def _short_path(path: str, max_parts: int = 3) -> str:
    """Shorten a file path for display."""
    parts = Path(path).parts
    if len(parts) <= max_parts:
        return str(Path(*parts))
    return str(Path("...", *parts[-max_parts:]))


def _make_relative_path(path: str, proj_a: str, proj_b: str) -> str:
    """Strip project root prefix to get relative path."""
    for prefix in (proj_a + "/", proj_b + "/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def _deduplicate_matches(
    matches: list,
    proj_a: str,
    proj_b: str,
) -> list[dict]:
    """Deduplicate matches by (func_a, func_b, file_a, file_b), keep highest sim."""
    deduped: dict[tuple, dict] = {}
    for m in matches:
        key = (m.function_a, m.function_b, m.file_a, m.file_b)
        if key not in deduped or m.similarity > deduped[key]["similarity"]:
            deduped[key] = {
                "type": m.similarity_type,
                "similarity": round(m.similarity, 2),
                "func_a": m.function_a,
                "func_b": m.function_b,
                "file_a": _make_relative_path(m.file_a, proj_a, proj_b),
                "file_b": _make_relative_path(m.file_b, proj_a, proj_b),
                "loc": max(m.lines_a[1] - m.lines_a[0], m.lines_b[1] - m.lines_b[0]),
            }

    # Sort by LOC descending, filter trivial
    sorted_matches = sorted(deduped.values(), key=lambda x: x["loc"], reverse=True)
    return [m for m in sorted_matches if m["loc"] > 2]


def _compact_community(
    c: "CodeCommunity",
    proj_a: str,
    proj_b: str,
) -> dict:
    """Convert community to compact dict format."""
    funcs: list[dict] = []
    for proj, node_key in c.members:
        # node_key format: "project::file::func"
        parts = node_key.split("::")
        func_name = parts[-1] if len(parts) >= 3 else parts[-1]
        file_path = parts[-2] if len(parts) >= 3 else ""
        funcs.append({
            "project": "A" if proj == proj_a else "B",
            "file": _make_relative_path(file_path, proj_a, proj_b),
            "function": func_name,
        })

    return {
        "name": c.extraction_candidate_name,
        "similarity": round(c.avg_similarity, 2),
        "loc": c.total_loc,
        "members": funcs,
    }


def _filter_significant_communities(
    communities: list["CodeCommunity"],
    proj_a: str,
    proj_b: str,
) -> list[dict]:
    """Convert communities to compact format and filter by significance."""
    compact = [_compact_community(c, proj_a, proj_b) for c in communities]
    significant = [c for c in compact if c["loc"] >= 8]
    return significant[:20]


def _build_recommendation_dict(
    comparison: "CrossProjectComparison",
    communities: list,
) -> dict | None:
    """Build recommendation dict or None if no communities."""
    if not communities:
        return None

    from redup.core.decision import recommend
    rec = recommend(comparison, communities)
    return {
        "decision": rec.decision.value,
        "rationale": rec.rationale,
        "overlap_pct": round(rec.overlap_percent, 4),
        "shared_loc": rec.shared_loc,
        "confidence": rec.confidence,
    }


def _build_json_report(
    comparison: "CrossProjectComparison",
    communities: list,
) -> dict:
    """Build a compact, human-readable JSON report.

    Optimisations vs. verbose format:
    - Relative file paths (strips project root prefix)
    - Matches deduplicated & grouped by function pair (keeps highest sim)
    - Communities: short member dicts instead of raw node keys
    - overlap_percent rounded to 4 decimals
    """
    proj_a = str(comparison.project_a)
    proj_b = str(comparison.project_b)

    significant_matches = _deduplicate_matches(comparison.matches, proj_a, proj_b)
    significant_communities = _filter_significant_communities(communities, proj_a, proj_b)
    recommendation = _build_recommendation_dict(comparison, communities)

    return {
        "project_a": proj_a,
        "project_b": proj_b,
        "stats": {
            "a": comparison.stats_a,
            "b": comparison.stats_b,
        },
        "total_matches": len(significant_matches),
        "shared_loc_potential": comparison.shared_loc_potential,
        "recommendation": recommendation,
        "communities": significant_communities,
        "matches": significant_matches,
    }
