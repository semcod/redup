"""Tests for reDUP reporters."""

import json

from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    ScanStats,
)
from redup.reporters.json_reporter import to_json
from redup.reporters.toon_reporter import to_toon
from redup.reporters.yaml_reporter import to_yaml


def _sample_map() -> DuplicationMap:
    return DuplicationMap(
        project_path="/tmp/test",
        groups=[
            DuplicateGroup(
                id="E0001",
                duplicate_type=DuplicateType.EXACT,
                normalized_name="calculate_tax",
                normalized_hash="abc123",
                fragments=[
                    DuplicateFragment(
                        file="billing.py", line_start=1, line_end=8,
                        function_name="calculate_tax",
                    ),
                    DuplicateFragment(
                        file="shipping.py", line_start=1, line_end=8,
                        function_name="calculate_tax",
                    ),
                ],
            ),
        ],
        stats=ScanStats(files_scanned=4, total_lines=100, total_blocks=20, scan_time_ms=42.5),
    )


def test_json_reporter_valid_json():
    dm = _sample_map()
    output = to_json(dm)
    data = json.loads(output)
    assert data["summary"]["total_groups"] == 1
    assert data["summary"]["total_saved_lines"] == 8
    assert len(data["groups"]) == 1
    assert data["groups"][0]["id"] == "E0001"
    assert len(data["refactor_suggestions"]) == 0  # no suggestions without planner


def test_json_reporter_with_suggestions():
    dm = _sample_map()
    # Generate suggestions via planner
    from redup.core.planner import generate_suggestions
    dm.suggestions = generate_suggestions(dm)

    output = to_json(dm)
    data = json.loads(output)
    assert len(data["refactor_suggestions"]) >= 1
    assert data["refactor_suggestions"][0]["priority"] == 1


def test_toon_reporter_header():
    dm = _sample_map()
    output = to_toon(dm)
    assert output.startswith("# redup/duplication")
    assert "1 groups" in output
    assert "DUPLICATES[1]" in output


def test_toon_reporter_contains_fragments():
    dm = _sample_map()
    output = to_toon(dm)
    assert "billing.py" in output
    assert "shipping.py" in output
    assert "calculate_tax" in output


def test_yaml_reporter_valid():
    dm = _sample_map()
    output = to_yaml(dm)
    assert "project_path:" in output
    assert "groups:" in output
    assert "E0001" in output


def test_empty_map_json():
    dm = DuplicationMap()
    output = to_json(dm)
    data = json.loads(output)
    assert data["summary"]["total_groups"] == 0
    assert data["groups"] == []


def test_empty_map_toon():
    dm = DuplicationMap()
    output = to_toon(dm)
    assert "0 groups" in output


# ── New toon sections tests ─────────────────────────────────────────


def _rich_map() -> DuplicationMap:
    """Sample map with cross-package duplicates for testing all toon sections."""
    from redup.core.planner import generate_suggestions

    dm = DuplicationMap(
        project_path="/tmp/test",
        groups=[
            # Large cross-package duplicate → triggers DEPENDENCY_RISK + HOTSPOTS
            DuplicateGroup(
                id="G001",
                duplicate_type=DuplicateType.EXACT,
                normalized_name="validate_input",
                normalized_hash="aaa",
                fragments=[
                    DuplicateFragment(
                        file="api/routes/users.py", line_start=10, line_end=45,
                        function_name="validate_input",
                    ),
                    DuplicateFragment(
                        file="services/auth/validate.py", line_start=5, line_end=40,
                        function_name="validate_input",
                    ),
                ],
            ),
            # Medium same-package duplicate → triggers QUICK_WINS (low risk)
            DuplicateGroup(
                id="G002",
                duplicate_type=DuplicateType.STRUCTURAL,
                normalized_name="format_date",
                normalized_hash="bbb",
                fragments=[
                    DuplicateFragment(
                        file="utils/dates.py", line_start=1, line_end=14,
                        function_name="format_date",
                    ),
                    DuplicateFragment(
                        file="utils/display.py", line_start=20, line_end=33,
                        function_name="format_date_display",
                    ),
                ],
            ),
            # Small duplicate → still shows in EFFORT_ESTIMATE
            DuplicateGroup(
                id="G003",
                duplicate_type=DuplicateType.EXACT,
                normalized_name="get_logger",
                normalized_hash="ccc",
                fragments=[
                    DuplicateFragment(
                        file="api/main.py", line_start=1, line_end=8,
                        function_name="get_logger",
                    ),
                    DuplicateFragment(
                        file="services/main.py", line_start=1, line_end=8,
                        function_name="get_logger",
                    ),
                ],
            ),
        ],
        stats=ScanStats(files_scanned=10, total_lines=2000, total_blocks=50, scan_time_ms=100),
    )
    dm.suggestions = generate_suggestions(dm)
    return dm


def test_toon_hotspots():
    dm = _rich_map()
    output = to_toon(dm)
    assert "HOTSPOTS[" in output
    assert "api/routes/users.py" in output
    assert "dup=" in output


def test_toon_dependency_risk():
    dm = _rich_map()
    output = to_toon(dm)
    assert "DEPENDENCY_RISK[" in output
    assert "validate_input" in output
    assert "packages=" in output


def test_toon_quick_wins():
    dm = _rich_map()
    output = to_toon(dm)
    assert "QUICK_WINS[" in output
    assert "saved=" in output


def test_toon_effort_estimate():
    dm = _rich_map()
    output = to_toon(dm)
    assert "EFFORT_ESTIMATE" in output
    assert "easy" in output or "medium" in output or "hard" in output
    assert "~" in output  # time estimate


def test_toon_empty_map_no_new_sections():
    dm = DuplicationMap()
    output = to_toon(dm)
    assert "HOTSPOTS" not in output
    assert "DEPENDENCY_RISK" not in output
    assert "QUICK_WINS" not in output
    assert "EFFORT_ESTIMATE" not in output


def test_toon_single_package_no_dependency_risk():
    """Duplicates within one package should not trigger DEPENDENCY_RISK."""
    dm = DuplicationMap(
        project_path="/tmp/test",
        groups=[
            DuplicateGroup(
                id="X001",
                duplicate_type=DuplicateType.EXACT,
                normalized_name="helper",
                normalized_hash="xxx",
                fragments=[
                    DuplicateFragment(file="utils/a.py", line_start=1, line_end=10, function_name="helper"),
                    DuplicateFragment(file="utils/b.py", line_start=1, line_end=10, function_name="helper"),
                ],
            ),
        ],
        stats=ScanStats(files_scanned=2, total_lines=200),
    )
    output = to_toon(dm)
    assert "DEPENDENCY_RISK" not in output
