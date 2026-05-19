"""Quality-gate commands for the reDUP CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import typer

app = typer.Typer(help="Run local quality gates.")

DEFAULT_JSCPD_PATHS = (
    "src",
    "tests",
    "test_fuzzy_similarity.py",
    "test_universal_fuzzy.py",
    "scripts",
    "benchmark.py",
)


@dataclass(frozen=True)
class JscpdStats:
    groups: int
    duplicated_lines: int
    percentage: float


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return default if value is None else int(value)


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default))


def _repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return Path.cwd()


def _jscpd_command(cwd: Path) -> list[str]:
    if shutil.which("jscpd"):
        return ["jscpd"]

    if shutil.which("npx"):
        no_install = subprocess.run(
            ["npx", "--no-install", "jscpd", "--version"],
            cwd=cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if no_install.returncode == 0:
            return ["npx", "--no-install", "jscpd"]
        return ["npx", "--yes", "jscpd"]

    raise RuntimeError(
        "[jscpd] CLI not available. Install globally with: npm install -g jscpd "
        "or run in an environment with npx available."
    )


def _read_jscpd_stats(report_path: Path) -> JscpdStats:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    stats = payload.get("statistics", {}).get("total", {})
    return JscpdStats(
        groups=int(stats.get("clones", 0)),
        duplicated_lines=int(stats.get("duplicatedLines", 0)),
        percentage=float(stats.get("percentage", 0.0)),
    )


def _budget_violations(stats: JscpdStats, max_groups: int, max_lines: int) -> list[str]:
    violations = []
    if stats.groups > max_groups:
        violations.append(f"groups {stats.groups} > {max_groups}")
    if stats.duplicated_lines > max_lines:
        violations.append(f"duplicated_lines {stats.duplicated_lines} > {max_lines}")
    return violations


def run_jscpd_budget(
    paths: list[Path],
    min_lines: int,
    max_groups: int,
    max_lines: int,
    report_dir: Path,
    silent: bool = True,
) -> JscpdStats:
    root = _repo_root()
    report_dir.mkdir(parents=True, exist_ok=True)

    command = [
        *_jscpd_command(root),
        *(str(path) for path in paths),
        "--reporters",
        "json,console",
        "--output",
        str(report_dir),
        "--min-lines",
        str(min_lines),
    ]
    if silent:
        command.append("--silent")

    subprocess.run(command, cwd=root, check=False)

    report_path = report_dir / "jscpd-report.json"
    if not report_path.is_file():
        raise RuntimeError(f"[jscpd] Error: report not generated at {report_path}")

    stats = _read_jscpd_stats(report_path)
    violations = _budget_violations(stats, max_groups, max_lines)

    typer.echo(
        f"[jscpd] total_groups={stats.groups} duplicated_lines={stats.duplicated_lines} "
        f"percentage={stats.percentage:.2f}% "
        f"(budget: groups<={max_groups}, lines<={max_lines})"
    )

    if violations:
        raise RuntimeError(f"[jscpd] budget exceeded: {', '.join(violations)}")

    typer.echo("[jscpd] budget OK")
    return stats


@app.command(
    "jscpd-run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def jscpd_run(ctx: typer.Context) -> None:
    """Run jscpd with local/global/npx fallback."""
    root = _repo_root()
    try:
        result = subprocess.run([*_jscpd_command(root), *ctx.args], cwd=root, check=False)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(127) from exc
    raise typer.Exit(result.returncode)


@app.command()
def jscpd(
    paths: list[Path] | None = typer.Argument(
        None,
        help="Paths to scan. Defaults to reDUP's source, tests, scripts, and benchmark files.",
    ),
    min_lines: int | None = typer.Option(
        None,
        "--min-lines",
        help="Minimum clone size. Defaults to JSCPD_MIN_LINES or 10.",
    ),
    max_groups: int | None = typer.Option(
        None,
        "--max-groups",
        help="Maximum allowed duplicate groups. Defaults to JSCPD_MAX_GROUPS or 15.",
    ),
    max_lines: int | None = typer.Option(
        None,
        "--max-lines",
        help="Maximum allowed duplicated lines. Defaults to JSCPD_MAX_LINES or 200.",
    ),
    report_dir: Path | None = typer.Option(
        None,
        "--report-dir",
        help="Directory for the jscpd JSON report. Defaults to JSCPD_REPORT_DIR or .jscpd.",
    ),
    silent: bool = typer.Option(True, "--silent/--no-silent", help="Pass --silent to jscpd."),
) -> None:
    """Run jscpd and enforce a duplicate-code budget."""
    selected_paths = paths or [Path(path) for path in DEFAULT_JSCPD_PATHS]
    try:
        run_jscpd_budget(
            paths=selected_paths,
            min_lines=min_lines if min_lines is not None else _env_int("JSCPD_MIN_LINES", 10),
            max_groups=(
                max_groups if max_groups is not None else _env_int("JSCPD_MAX_GROUPS", 15)
            ),
            max_lines=max_lines if max_lines is not None else _env_int("JSCPD_MAX_LINES", 200),
            report_dir=(
                report_dir if report_dir is not None else _env_path("JSCPD_REPORT_DIR", ".jscpd")
            ),
            silent=silent,
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
