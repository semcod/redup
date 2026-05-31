import sys
import types
from pathlib import Path

import pytest

from redup.core.models import DuplicateType, ScanConfig
from redup.core.pipeline.duplicate_finder import find_intent_groups
from redup.core.scanner_types import CodeBlock

from redup.integrations.intract.adapter import detect_intent_duplicates, _resolve_manifest_path


def _block(file_path: str, content: str, *, line_start: int = 1, line_end: int = 10) -> CodeBlock:
    return CodeBlock(
        file=file_path,
        line_start=line_start,
        line_end=line_end,
        text=content,
        function_name="example",
    )


def _install_fake_intract(monkeypatch, groups_payload):
    fake_redup = types.ModuleType("intract.integrations.redup")
    fake_redup.find_intent_duplicate_groups = lambda **kwargs: groups_payload
    fake_integrations = types.ModuleType("intract.integrations")
    fake_integrations.redup = fake_redup
    fake_intract = types.ModuleType("intract")
    fake_intract.integrations = fake_integrations

    monkeypatch.setitem(sys.modules, "intract", fake_intract)
    monkeypatch.setitem(sys.modules, "intract.integrations", fake_integrations)
    monkeypatch.setitem(sys.modules, "intract.integrations.redup", fake_redup)


def test_duplicate_type_intent_exists():
    assert DuplicateType.INTENT.value == "intent"


def test_detect_intent_duplicates_maps_groups(tmp_path: Path, monkeypatch):
    payload = [
        {
            "group_id": "intent_0001",
            "similarity": 0.91,
            "fragments": [
                {"file_path": "a.py", "start_line": 1, "end_line": 3},
                {"file_path": "b.py", "start_line": 1, "end_line": 3},
            ],
            "metadata": {"duplicate_type": "intent"},
            "evidence": {"contracts": ["parse.extensions", "parse.extension_list"]},
        }
    ]
    _install_fake_intract(monkeypatch, payload)

    blocks = [
        _block("a.py", "def a(): pass", line_start=1, line_end=3),
        _block("b.py", "def b(): pass", line_start=1, line_end=3),
    ]
    config = ScanConfig(root=tmp_path, intent_enabled=True, intent_threshold=0.5)
    groups = detect_intent_duplicates(blocks, config)

    assert len(groups) == 1
    assert groups[0].duplicate_type == DuplicateType.INTENT
    assert groups[0].id == "intent_0001"
    assert groups[0].metadata.get("engine") == "intract"
    assert groups[0].occurrences == 2


def test_resolve_manifest_path(tmp_path: Path):
    manifest = tmp_path / "intract.yaml"
    manifest.write_text("contracts: []\n", encoding="utf-8")
    config = ScanConfig(root=tmp_path, intent_manifest_path=Path("intract.yaml"))
    assert _resolve_manifest_path(config) == str(manifest)


def test_find_intent_groups_disabled():
    blocks = [
        _block("a.py", "# @intract.v1 scope:function intent:parse:extensions\npass"),
    ]
    config = ScanConfig(intent_enabled=False)
    assert find_intent_groups(blocks, config) == []


def test_validate_for_redup_policy_helper(tmp_path: Path):
    pytest.importorskip("intract")
    from intract.integrations.redup import validate_for_redup

    manifest = tmp_path / "intract.yaml"
    manifest.write_text("project:\n  name: demo\ncontracts: []\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")

    result = validate_for_redup(tmp_path, manifest=manifest, fail_on=["violation"], warn_on=["partial"])
    assert not result.should_fail


def test_apply_scan_intent_policy_with_duplicates(tmp_path: Path, monkeypatch):
    pytest.importorskip("intract")
    from redup.cli_app.intract_commands import apply_scan_intent_policy
    from redup.core.models import DuplicateGroup, DuplicateType, DuplicationMap, ScanConfig

    config = ScanConfig(root=tmp_path, intent_enabled=True, intent_fail_on="intent_duplicate")
    manifest = tmp_path / "intract.yaml"
    manifest.write_text("project:\n  name: demo\ncontracts: []\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")

    dup_map = DuplicationMap(
        groups=[
            DuplicateGroup(
                id="I0001",
                duplicate_type=DuplicateType.INTENT,
                fragments=[],
                similarity_score=0.9,
                metadata={"evidence": {"contracts": ["a.b", "c.d"]}},
            )
        ]
    )

    result = apply_scan_intent_policy(tmp_path, config, dup_map)
    assert result.should_fail
    assert result.intent_duplicate_groups == 1
