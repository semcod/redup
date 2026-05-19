"""Tests for packaged quality-gate CLI commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from redup.cli_app import quality_commands
from redup.cli_app.main import app

runner = CliRunner()


def test_read_jscpd_stats(tmp_path: Path) -> None:
    report = tmp_path / "jscpd-report.json"
    report.write_text(
        json.dumps(
            {
                "statistics": {
                    "total": {
                        "clones": 3,
                        "duplicatedLines": 44,
                        "percentage": 0.33,
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    stats = quality_commands._read_jscpd_stats(report)

    assert stats.groups == 3
    assert stats.duplicated_lines == 44
    assert stats.percentage == 0.33


def test_budget_violations() -> None:
    stats = quality_commands.JscpdStats(groups=4, duplicated_lines=54, percentage=0.4)

    assert quality_commands._budget_violations(stats, max_groups=4, max_lines=60) == []
    assert quality_commands._budget_violations(stats, max_groups=3, max_lines=40) == [
        "groups 4 > 3",
        "duplicated_lines 54 > 40",
    ]


def test_run_jscpd_budget_invokes_fallback_and_reads_report(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        report_dir = Path(command[command.index("--output") + 1])
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "jscpd-report.json").write_text(
            json.dumps(
                {
                    "statistics": {
                        "total": {
                            "clones": 2,
                            "duplicatedLines": 20,
                            "percentage": 0.2,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(quality_commands, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(quality_commands, "_jscpd_command", lambda cwd: ["jscpd"])
    monkeypatch.setattr(quality_commands.subprocess, "run", fake_run)

    stats = quality_commands.run_jscpd_budget(
        paths=[Path("src")],
        min_lines=10,
        max_groups=3,
        max_lines=30,
        report_dir=tmp_path / ".jscpd",
    )

    assert stats.groups == 2
    assert calls == [
        [
            "jscpd",
            "src",
            "--reporters",
            "json,console",
            "--output",
            str(tmp_path / ".jscpd"),
            "--min-lines",
            "10",
            "--silent",
        ]
    ]


def test_quality_jscpd_cli_uses_packaged_command(monkeypatch) -> None:
    received = {}

    def fake_run_jscpd_budget(**kwargs):
        received.update(kwargs)
        return quality_commands.JscpdStats(groups=0, duplicated_lines=0, percentage=0.0)

    monkeypatch.setattr(quality_commands, "run_jscpd_budget", fake_run_jscpd_budget)

    result = runner.invoke(
        app,
        [
            "quality",
            "jscpd",
            "src",
            "--min-lines",
            "8",
            "--max-groups",
            "5",
            "--max-lines",
            "80",
            "--report-dir",
            ".dups",
            "--no-silent",
        ],
    )

    assert result.exit_code == 0
    assert received == {
        "paths": [Path("src")],
        "min_lines": 8,
        "max_groups": 5,
        "max_lines": 80,
        "report_dir": Path(".dups"),
        "silent": False,
    }
