"""Tests for the reDUP MCP server."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from redup.core.models import ScanConfig
from redup.core.pipeline import analyze
from redup.mcp import handlers as mcp_handlers
from redup.mcp.handlers import _build_scan_config
from redup.mcp_server import handle_request
from redup.reporters.json_reporter import to_json


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
        """def something_unique():
    x = [i**2 for i in range(100)]
    return sum(x)
""",
        encoding="utf-8",
    )


def _analyze_test_project(root: Path):
    config = ScanConfig(root=root, min_block_lines=3, min_similarity=0.80)
    return analyze(config=config, function_level_only=True)


def test_initialize_and_tools_list() -> None:
    init_response = handle_request({"jsonrpc": "2.0", "method": "initialize", "id": 1})
    assert init_response["result"]["protocolVersion"] == "2024-11-05"
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

    compare_tool = next(
        tool for tool in tools_response["result"]["tools"] if tool["name"] == "compare_projects"
    )
    assert compare_tool["inputSchema"]["required"] == ["project_a", "project_b"]
    find_tool = next(
        tool for tool in tools_response["result"]["tools"] if tool["name"] == "find_duplicates"
    )
    assert find_tool["inputSchema"]["properties"]["max_groups"]["default"] == 10
    analyze_tool = next(
        tool for tool in tools_response["result"]["tools"] if tool["name"] == "analyze_project"
    )
    scan_properties = analyze_tool["inputSchema"]["properties"]
    assert "parallel" not in scan_properties
    assert "leading dots are optional" in scan_properties["extensions"]["description"]


def test_mcp_scan_config_accepts_semantic_options(tmp_path: Path) -> None:
    config = _build_scan_config(
        tmp_path,
        {
            "semantic": True,
            "semantic_threshold": 0.74,
            "semantic_model": "example/code-model",
        },
    )

    assert config.semantic_enabled is True
    assert config.semantic_threshold == 0.74
    assert config.semantic_model == "example/code-model"


def test_project_info_checks_optional_packages_without_importing(monkeypatch) -> None:
    checked = []

    def fake_find_spec(module: str):
        checked.append(module)
        return object()

    monkeypatch.setattr(mcp_handlers.importlib.util, "find_spec", fake_find_spec)

    payload = json.loads(mcp_handlers.handle_project_info({}))

    assert "sentence_transformers" in checked
    assert all(payload["optional_dependencies"].values())
    assert payload["semantic_defaults"]["model"].startswith("sentence-transformers/")
    assert payload["semantic_defaults"]["fallback"] == "redup/intent-profile-v1"


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
        assert payload["selection"]["group_scope"] == "non_generated"


def test_llm_mcp_payload_normalizes_comma_separated_extensions(
    tmp_path: Path, monkeypatch
) -> None:
    """Exercise the public MCP route with the argument shape emitted by LLM clients."""
    for name, source in {
        "sample.py": "def python_sample():\n    return 1\n",
        "sample.js": "function javascriptSample() { return 1; }\n",
        "sample.ts": "function typescriptSample(): number { return 1; }\n",
    }.items():
        (tmp_path / name).write_text(source, encoding="utf-8")

    captured: dict[str, object] = {}

    def analyze_without_optional_semantic_backend(
        config: ScanConfig, *, function_level_only: bool, max_workers: int | None
    ):
        captured["extensions"] = config.extensions
        captured["semantic_enabled"] = config.semantic_enabled
        config.semantic_enabled = False
        return analyze(config=config, function_level_only=function_level_only)

    monkeypatch.setattr(mcp_handlers, "analyze_parallel", analyze_without_optional_semantic_backend)
    mcp_handlers._ANALYSIS_CACHE.clear()

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 33,
            "params": {
                "name": "analyze_project",
                "arguments": {
                    "path": str(tmp_path),
                    "extensions": "py,js,ts",
                    "format": "json",
                    "functions_only": True,
                    "fuzzy": True,
                    "fuzzy_threshold": 0.86,
                    "include_snippets": False,
                    "include_tests": False,
                    "min_lines": 2,
                    "min_similarity": 0.86,
                    "mode": "parallel",
                    "parallel": True,
                    "semantic": True,
                    "semantic_threshold": 0.9,
                },
            },
        }
    )

    assert "error" not in response
    payload = json.loads(response["result"]["content"][0]["text"])
    assert captured == {
        "extensions": [".py", ".js", ".ts"],
        "semantic_enabled": True,
    }
    assert payload["stats"]["files_scanned"] == 3


def test_identical_mcp_analysis_uses_cache_until_source_changes(tmp_path: Path) -> None:
    mcp_handlers._ANALYSIS_CACHE.clear()
    _create_test_project(tmp_path)
    arguments = {
        "path": str(tmp_path),
        "format": "json",
        "mode": "standard",
        "functions_only": True,
    }

    first = json.loads(mcp_handlers.handle_analyze_project(arguments))
    second = json.loads(mcp_handlers.handle_analyze_project(arguments))
    assert first["execution"]["analysis_cache_hit"] is False
    assert second["execution"]["analysis_cache_hit"] is True

    with (tmp_path / "unique.py").open("a", encoding="utf-8") as source:
        source.write("\ndef another_unique():\n    return 42\n")

    third = json.loads(mcp_handlers.handle_analyze_project(arguments))
    assert third["execution"]["analysis_cache_hit"] is False


def test_compare_projects_scans_directories(tmp_path: Path) -> None:
    project_a = tmp_path / "a"
    project_b = tmp_path / "b"
    project_a.mkdir()
    project_b.mkdir()
    shared = "def shared(value):\n    result = value + 1\n    return result * 2\n"
    (project_a / "one.py").write_text(shared, encoding="utf-8")
    (project_b / "two.py").write_text(shared, encoding="utf-8")

    response = handle_request(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 31,
            "params": {
                "name": "compare_projects",
                "arguments": {
                    "project_a": str(project_a),
                    "project_b": str(project_b),
                    "extensions": "py",
                },
            },
        }
    )

    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["project_a"] == str(project_a)
    assert payload["project_b"] == str(project_b)
    assert payload["total_matches"] >= 1
    assert payload["matches"][0]["loc"] == 3


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


def test_tool_progress_output_cannot_corrupt_stdio_protocol(monkeypatch, capsys) -> None:
    def noisy_handler(_):
        print("progress from analysis")
        return "{}"

    monkeypatch.setitem(mcp_handlers.TOOL_HANDLERS, "noisy", noisy_handler)
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 99,
            "params": {"name": "noisy", "arguments": {}},
        }
    )

    captured = capsys.readouterr()
    assert response["result"]["content"][0]["text"] == "{}"
    assert captured.out == ""
    assert "progress from analysis" in captured.err
