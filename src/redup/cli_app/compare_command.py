"""Implementation of the ``redup compare`` CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

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

    ext_list = (
        [e.strip() for e in extensions.split(",")]
        if extensions
        else None
    )

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

    # ── Summary table ──────────────────────────────────────────────
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

    # ── Community detection (optional) ─────────────────────────────
    communities = []
    if not no_community and comparison.total_matches > 0:
        try:
            from redup.core.community import detect_communities
            communities = detect_communities(comparison, min_similarity=threshold)
        except ImportError:
            console.print(
                "[yellow]networkx not installed — skipping community detection. "
                "Install with: pip install redup[compare][/yellow]"
            )

    # ── Decision recommendation ────────────────────────────────────
    if communities or comparison.total_matches > 0:
        from redup.core.decision import recommend
        rec = recommend(comparison, communities)

        console.print()
        console.print(f"[bold green]Recommendation:[/bold green] {rec.decision.value}")
        console.print(f"[dim]{rec.rationale}[/dim]")
        console.print(f"[dim]Confidence: {rec.confidence:.0%}[/dim]")

        if communities:
            table2 = Table(title="Top Communities (shared code candidates)")
            table2.add_column("ID", justify="right")
            table2.add_column("Name")
            table2.add_column("Similarity", justify="right")
            table2.add_column("LOC", justify="right")
            table2.add_column("Members", justify="right")
            for c in communities[:10]:
                table2.add_row(
                    str(c.id),
                    c.extraction_candidate_name,
                    f"{c.avg_similarity:.2f}",
                    str(c.total_loc),
                    str(len(c.members)),
                )
            console.print(table2)
    else:
        console.print("\n[green]No cross-project duplicates found.[/green]")

    # ── Match details ──────────────────────────────────────────────
    if comparison.matches:
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

    # ── LLM refactoring plan ───────────────────────────────────────
    report = _build_json_report(comparison, communities)
    plan = None

    if refactor_plan and comparison.total_matches > 0:
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

        except ImportError as e:
            console.print(f"[yellow]{e}[/yellow]")
        except RuntimeError as e:
            console.print(f"[red]LLM error: {e}[/red]")

    # ── JSON export ────────────────────────────────────────────────
    if output:
        output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        console.print(f"\n[bold]Report saved to:[/bold] {output}")


def _short_path(path: str, max_parts: int = 3) -> str:
    """Shorten a file path for display."""
    parts = Path(path).parts
    if len(parts) <= max_parts:
        return str(Path(*parts))
    return str(Path("...", *parts[-max_parts:]))


def _build_json_report(comparison, communities) -> dict:
    """Build a compact, human-readable JSON report.

    Optimisations vs. verbose format:
    - Relative file paths (strips project root prefix)
    - Matches deduplicated & grouped by function pair (keeps highest sim)
    - Communities: short member dicts instead of raw node keys
    - overlap_percent rounded to 4 decimals
    """
    from redup.core.decision import recommend

    proj_a = str(comparison.project_a)
    proj_b = str(comparison.project_b)

    def _rel(path: str) -> str:
        """Strip project root prefix to get relative path."""
        for prefix in (proj_a + "/", proj_b + "/"):
            if path.startswith(prefix):
                return path[len(prefix):]
        return path

    rec = recommend(comparison, communities) if communities else None

    # ── Deduplicate matches by (func_a, func_b, file_a, file_b) ──
    deduped: dict[tuple, dict] = {}
    for m in comparison.matches:
        key = (m.function_a, m.function_b, m.file_a, m.file_b)
        if key not in deduped or m.similarity > deduped[key]["similarity"]:
            deduped[key] = {
                "type": m.similarity_type,
                "similarity": round(m.similarity, 2),
                "func_a": m.function_a,
                "func_b": m.function_b,
                "file_a": _rel(m.file_a),
                "file_b": _rel(m.file_b),
                "loc": max(m.lines_a[1] - m.lines_a[0], m.lines_b[1] - m.lines_b[0]),
            }

    # Sort by LOC descending
    sorted_matches = sorted(deduped.values(), key=lambda x: x["loc"], reverse=True)

    # ── Compact communities ──────────────────────────────────────
    compact_communities = []
    for c in communities:
        funcs: list[dict] = []
        for proj, node_key in c.members:
            # node_key format: "project::file::func"
            parts = node_key.split("::")
            func_name = parts[-1] if len(parts) >= 3 else parts[-1]
            file_path = parts[-2] if len(parts) >= 3 else ""
            funcs.append({
                "project": "A" if proj == proj_a else "B",
                "file": _rel(file_path),
                "function": func_name,
            })
        compact_communities.append({
            "name": c.extraction_candidate_name,
            "similarity": round(c.avg_similarity, 2),
            "loc": c.total_loc,
            "members": funcs,
        })

    # Filter noise: drop trivial entries, cap communities at top 20
    significant_matches = [m for m in sorted_matches if m["loc"] > 2]
    significant_communities = [c for c in compact_communities if c["loc"] >= 8][:20]

    return {
        "project_a": proj_a,
        "project_b": proj_b,
        "stats": {
            "a": comparison.stats_a,
            "b": comparison.stats_b,
        },
        "total_matches": len(significant_matches),
        "shared_loc_potential": comparison.shared_loc_potential,
        "recommendation": {
            "decision": rec.decision.value,
            "rationale": rec.rationale,
            "overlap_pct": round(rec.overlap_percent, 4),
            "shared_loc": rec.shared_loc,
            "confidence": rec.confidence,
        } if rec else None,
        "communities": significant_communities,
        "matches": significant_matches,
    }
