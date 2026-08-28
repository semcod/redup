"""Tests for CLI output format dispatch."""

import json
from pathlib import Path

from redup.cli_app.output_writer import write_results
from redup.core.models import DuplicationMap, ScanStats


def test_enhanced_output_is_valid_json_with_current_version(tmp_path: Path) -> None:
    output = tmp_path / "enhanced.json"
    dup_map = DuplicationMap(
        project_path=str(tmp_path),
        stats=ScanStats(files_scanned=1, total_lines=10, total_blocks=2, scan_time_ms=1.0),
    )

    write_results(dup_map, "enhanced", output, tmp_path)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["metadata"]["project_path"] == str(tmp_path)
    assert payload["metadata"]["redup_version"] != "0.3.2"
    assert "metrics" in payload
    assert "visualizations" in payload
