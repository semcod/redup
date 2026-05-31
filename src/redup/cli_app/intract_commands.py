"""reDUP intract CLI command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from redup.core.models import ScanConfig
from redup.integrations.intract.policy import run_intract_policy_check


def intract_command(
    path: Path = typer.Argument(Path("."), help="Project root to validate."),
    manifest: Optional[Path] = typer.Option(None, "--manifest", help="Path to intract.yaml / intent.yaml."),
    intent: bool = typer.Option(True, "--intent/--no-intent", help="Include intent duplicate groups in policy."),
    intent_threshold: float = typer.Option(0.84, "--intent-threshold", help="Intent duplicate threshold."),
    fail_on: Optional[str] = typer.Option(
        None,
        "--fail-on",
        help="Comma-separated fail tokens (violation,intent_duplicate,missing_required_p1,...).",
    ),
    warn_on: Optional[str] = typer.Option(
        None,
        "--warn-on",
        help="Comma-separated warn tokens (partial,unknown,intent_duplicate,...).",
    ),
    output_format: str = typer.Option("text", "--format", "-f", help="Output format: text|json"),
    exit_on_fail: bool = typer.Option(True, "--exit/--no-exit", help="Exit non-zero on policy failure."),
) -> None:
    """Validate Intract contracts and optional intent duplicate policy for a project."""
    from intract.integrations.redup import parse_policy_tokens

    config = ScanConfig(
        root=path,
        intent_enabled=intent,
        intent_threshold=intent_threshold,
        intent_manifest_path=manifest,
    )
    if fail_on:
        config.intent_fail_on = fail_on
    if warn_on:
        config.intent_warn_on = warn_on

    blocks = None
    if intent:
        from redup.core.pipeline.phases import process_blocks, scan_phase

        scanned_files, _stats = scan_phase(config)
        blocks = process_blocks(scanned_files, config.functions_only)

    try:
        result = run_intract_policy_check(
            path,
            config,
            blocks=blocks,
            fail_on=parse_policy_tokens(fail_on) or None,
            warn_on=parse_policy_tokens(warn_on) or None,
        )
    except ImportError:
        typer.echo(
            "Error: Intract is not installed. Install with: pip install 'redup[intent]'",
            err=True,
        )
        raise typer.Exit(1) from None

    if output_format == "json":
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        lines = [
            "REDUP INTRACT CHECK",
            "",
            f"Validation status: {result.validation_status}",
            f"Intent duplicate groups: {result.intent_duplicate_groups}",
        ]
        if result.reasons:
            lines.extend(["", "FAIL REASONS:"])
            lines.extend(f"- {item}" for item in result.reasons)
        if result.warnings:
            lines.extend(["", "WARNINGS:"])
            lines.extend(f"- {item}" for item in result.warnings)
        typer.echo("\n".join(lines))

    if exit_on_fail and result.should_fail:
        raise typer.Exit(1)


def apply_scan_intent_policy(path: Path, config: ScanConfig, dup_map) -> "RedupPolicyResult":
    from intract.integrations.redup import validate_for_redup
    from redup.integrations.intract.adapter import _resolve_manifest_path
    from redup.integrations.intract.policy import intent_groups_from_dup_map, resolve_intract_policy

    resolved_fail_on, resolved_warn_on = resolve_intract_policy(config)
    manifest = _resolve_manifest_path(config)
    intent_groups = intent_groups_from_dup_map(dup_map)
    return validate_for_redup(
        path,
        manifest=manifest,
        intent_groups=intent_groups,
        fail_on=resolved_fail_on,
        warn_on=resolved_warn_on,
    )
