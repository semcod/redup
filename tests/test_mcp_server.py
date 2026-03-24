"""Tests for the reDUP MCP server."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from redup.mcp_server import handle_request
from redup.reporters.json_reporter import to_json
from redup.core.models import ScanConfig
from redup.core.pipeline import analyze


def _create_test_project(root: Path) -> None:
    (root / "billing.py").write_text(
        '''def calculate_tax(amount, rate):
    """Calculate tax for given amount."""
    if amount <= 0:
        return 0.0
    tax = amount * rate
    if tax > 1000:
        tax = 1000
    return round(tax, 2)


def process_payment(amount):
    return amount * 1.1
''',
        encoding="utf-8",
    )

    (root / "shipping.py").write_text(
        '''def calculate_tax(total, tax_rate):
    """Calculate tax for given amount."""
    if total <= 0:
        return 0.0
    tax = total * tax_rate
    if tax > 1000:
        tax = 1000
    return round(tax, 2)


def get_shipping_cost(weight):
    return weight * 2.5
''',
        encoding="utf-8",
    )

    (root / "returns.py").write_text(
        '''def calculate_tax(value, rate):
    """Calculate tax for given amount."""
    if value <= 0:
        return 0.0
    tax = value * rate
    if tax > 1000:
        tax = 1000
    return round(tax, 2)


def process_return(item_id):
    return f"returned_{item_id}"
''',
        encoding="utf-8",
    )

    (root / "unique.py").write_text(
        '''def something_unique():
    x = [i**2 for i in range(100)]
    return sum(x)
''',
        encoding="utf-8",
    )


def _analyze_test_project(root: Path):
    config = ScanConfig(root=root, min_block_lines=3, min_similarity=0.80)
    return analyze(config=config, function_level_only=True)


def test_initialize_and_tools_list() -> None:
    init_response = handle_request({"jsonrpc": "2.0", "method": "initialize", "id": 1})
    assert init_response["result"]["serverInfo"]["name"] == "redup"
    assert init_response["result"]["serverInfo"]["version"]

    tools_response = handle_request({"jsonrpc": "2.0", "method": "tools/list", "id": 2})
    tool_names = {tool["name"] for tool in tools_response["result"]["tools"]}

    assert {
        "analyze_project",
        "find_duplicates",
        "compare_scans",
        "compare_projects",
        "check_project",
        "suggest_refactoring",
        "project_info",
    } <= tool_names


def test_analyze_project_returns_json_report() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _create_test_project(root)

        response = handle_request(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 3,
                "params": {
                    "name": "analyze_project",
                    "arguments": {
                        "path": str(root),
                        "format": "json",
                        "mode": "standard",
                        "functions_only": True,
                    },
                },
            }
        )

        assert "result" in response
        payload = json.loads(response["result"]["content"][0]["text"])
        assert payload["project_path"] == str(root)
        assert payload["summary"]["total_groups"] >= 1


def test_compare_scans_returns_summary() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _create_test_project(root)

        dup_map = _analyze_test_project(root)
        before_path = root / "before.json"
        after_path = root / "after.json"
        before_path.write_text(to_json(dup_map), encoding="utf-8")
        after_path.write_text(to_json(dup_map), encoding="utf-8")

        response = handle_request(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 4,
                "params": {
                    "name": "compare_scans",
                    "arguments": {
                        "before": str(before_path),
                        "after": str(after_path),
                    },
                },
            }
        )

        payload = json.loads(response["result"]["content"][0]["text"])
        assert payload["success"] is True
        assert payload["summary"]["unchanged_count"] >= 1
        assert payload["summary"]["resolved_count"] == 0
        assert payload["summary"]["new_count"] == 0


def test_check_project_detects_threshold_violation() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _create_test_project(root)

        response = handle_request(
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "id": 5,
                "params": {
                    "name": "check_project",
                    "arguments": {
                        "path": str(root),
                        "max_groups": 0,
                        "max_lines": 0,
                        "mode": "standard",
                    },
                },
            }
        )

        payload = json.loads(response["result"]["content"][0]["text"])
        assert payload["success"] is True
        assert payload["passed"] is False
        assert payload["violations"]


def test_unknown_tool_returns_error() -> None:
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 6,
            "params": {"name": "missing_tool", "arguments": {}},
        }
    )

    assert response["error"]["code"] == -32601
