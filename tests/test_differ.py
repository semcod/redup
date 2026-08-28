"""Regression tests for loading and comparing saved JSON reports."""

import json
from pathlib import Path

from redup.core.differ import _load_duplication_map, compare_scans
from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    RefactorAction,
    RefactorSuggestion,
    RiskLevel,
    ScanStats,
)
from redup.reporters.json_reporter import to_json


def _saved_map() -> DuplicationMap:
    group = DuplicateGroup(
        id="E0001",
        duplicate_type=DuplicateType.EXACT,
        normalized_name="shared_parser",
        normalized_hash="abc123",
        metadata={"actionability": "refactor"},
        fragments=[
            DuplicateFragment("one.py", 1, 5, function_name="shared_parser"),
            DuplicateFragment("two.py", 10, 14, function_name="shared_parser"),
        ],
    )
    suggestion = RefactorSuggestion(
        group_id=group.id,
        action=RefactorAction.EXTRACT_CLASS,
        new_module="shared/parser.py",
        class_name="SharedParser",
        original_files=["one.py", "two.py"],
        risk_level=RiskLevel.MEDIUM,
        priority=1,
        rationale="Remove copied parsing behavior.",
    )
    return DuplicationMap(
        project_path="/tmp/example",
        groups=[group],
        suggestions=[suggestion],
        stats=ScanStats(files_scanned=2, total_lines=20, total_blocks=2, scan_time_ms=1.5),
    )


def test_saved_full_report_round_trips_suggestions_and_stats(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(to_json(_saved_map()), encoding="utf-8")

    loaded = _load_duplication_map(report_path)

    assert loaded.stats.files_scanned == 2
    assert loaded.groups[0].metadata["actionability"] == "refactor"
    assert loaded.suggestions[0].group_id == "E0001"
    assert loaded.suggestions[0].action is RefactorAction.EXTRACT_CLASS
    assert loaded.suggestions[0].risk_level is RiskLevel.MEDIUM
    assert loaded.suggestions[0].class_name == "SharedParser"


def test_compare_scans_accepts_compact_reports_without_hashes(tmp_path: Path) -> None:
    report = json.loads(to_json(_saved_map(), compact=True))
    assert "normalized_hash" not in report["groups"][0]
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    serialized = json.dumps(report)
    before_path.write_text(serialized, encoding="utf-8")
    after_path.write_text(serialized, encoding="utf-8")

    diff = compare_scans(before_path, after_path)

    assert diff.unchanged_count == 1
    assert diff.resolved_count == 0
    assert diff.new_count == 0
