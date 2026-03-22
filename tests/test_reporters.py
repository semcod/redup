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
