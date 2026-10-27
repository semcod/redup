"""Consumer regressions for source-bound cross-project evidence."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest

from redup.core.comparator import CrossProjectComparison, compare_projects
from redup.core.comparison_evidence import source_observation
from redup.core.scanner_types import CodeBlock, ScannedFile
from redup.reporters.comparison_reporter import comparison_to_dict

FUNCTION = "def double(value):\n    result = value * 2\n    return result\n"


@pytest.fixture
def projects(tmp_path):
    roots = [tmp_path / "a", tmp_path / "b"]
    for root in roots:
        root.mkdir()
        (root / "code.py").write_text(FUNCTION)
    return roots


def report(projects, **kwargs):
    return comparison_to_dict(compare_projects(*projects, **kwargs), [])


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def commit(root):
    git(root, "add", "code.py")
    git(
        root,
        "-c",
        "user.name=Evidence Test",
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "-qm",
        "fixture",
    )
    return git(root, "rev-parse", "HEAD")


def test_identical_reruns_and_reverse_pair_have_stable_ids(projects):
    first = report(projects)
    assert first == report(projects)
    candidate = first["evidence"]["candidates"][0]
    assert candidate["id"] == report(projects[::-1])["evidence"]["candidates"][0]["id"]
    assert candidate["source_a"]["file_sha256"] == hashlib.sha256(FUNCTION.encode()).hexdigest()
    assert candidate["source_a"]["lines"] == [1, 3]
    assert candidate["usable_source_evidence"]
    assert candidate["semantic_equivalence"] == "unknown"
    assert candidate["quality_winner"] is None
    assert first["evidence"]["sources"]["a"]["revision_freshness"] == "unknown"
    assert first["evidence"]["sources"]["a"]["coverage"]["behavioral_tests"] == "unknown"


def test_changed_source_cannot_reuse_a_fresh_candidate(projects):
    comparison = compare_projects(*projects)
    before = comparison_to_dict(comparison, [])["evidence"]
    (projects[0] / "code.py").write_text(FUNCTION.replace("* 2", "* 3"))
    after = comparison_to_dict(comparison, [])["evidence"]
    assert after["candidates"][0]["id"] == before["candidates"][0]["id"]
    assert after["candidates"][0]["source_a"]["freshness"] == "stale"
    assert not after["candidates"][0]["usable_source_evidence"]
    assert after["sources"]["a"]["coverage"]["files_current"] == 0
    # A stale serialization must not mutate the original scan.
    assert comparison.sources["a"]["files"]["code.py"]["freshness"] == "current"


def test_missing_source_is_unknown_not_fresh(projects):
    comparison = compare_projects(*projects)
    (projects[0] / "code.py").unlink()
    candidate = comparison_to_dict(comparison, [])["evidence"]["candidates"][0]
    assert candidate["source_a"]["freshness"] == "unknown"
    assert not candidate["usable_source_evidence"]


def test_capture_rejects_file_changed_after_scan(projects):
    root = projects[0]
    block = CodeBlock(str(root / "code.py"), 1, 3, FUNCTION.rstrip(), "double")
    scanned = ScannedFile(block.file, FUNCTION.splitlines(), [block])
    (root / "code.py").write_text(FUNCTION.replace("* 2", "* 3"))
    observation = source_observation(root, [scanned], [block], None)
    assert observation["files"]["code.py"]["file_sha256"] is None
    assert observation["files"]["code.py"]["freshness"] == "stale"
    assert observation["coverage"]["files_bound"] == 0


def test_observed_git_head_does_not_claim_dirty_content_is_committed(projects):
    root = projects[0]
    git(root, "init", "-q")
    head = commit(root)
    (root / "code.py").write_text(FUNCTION + "\n# local change\n")
    comparison = compare_projects(*projects)
    source = comparison_to_dict(comparison, [])["evidence"]["sources"]["a"]
    assert source["observed_head"] == head
    assert len(head) == 40
    assert source["revision_binding"] == "observed_head_only"
    commit(root)
    stale = comparison_to_dict(comparison, [])["evidence"]
    assert stale["sources"]["a"]["revision_freshness"] == "stale"
    assert not stale["candidates"][0]["usable_source_evidence"]


def test_generated_and_deployment_origins_require_explicit_declarations(projects):
    candidate = report(
        projects, origins_a={"code.py": "generated_copy"}, origins_b={"code.py": "deployment_copy"}
    )["evidence"]["candidates"][0]
    assert candidate["source_a"]["origin"] == "generated_copy"
    assert candidate["source_b"]["origin"] == "deployment_copy"
    assert candidate["source_a"]["origin_evidence"] == "caller_declaration"
    assert candidate["quality_winner"] is None
    assert report(projects)["evidence"]["candidates"][0]["source_a"]["origin"] == "unknown"
    with pytest.raises(ValueError, match="relative paths"):
        report(projects, origins_a={"../code.py": "authored"})


def test_optional_engines_missing_remain_unknown(projects, monkeypatch):
    monkeypatch.setitem(sys.modules, "redup.core.semantic", None)
    monkeypatch.setitem(sys.modules, "intract.integrations.redup", None)
    evidence = report(projects, use_semantic=True, use_intent=True)["evidence"]
    for engine in ("semantic", "declared_intent"):
        assert evidence["analysis"][engine]["status"] == "unavailable"
        assert evidence["analysis"][engine]["reason"] == "optional_dependency_missing"
    assert all(c["intent_evidence"] == "unknown" for c in evidence["candidates"])


def test_semantic_initialization_failure_does_not_erase_source_matches(projects, monkeypatch):
    module = types.ModuleType("redup.core.semantic")

    def unavailable(**kwargs):
        raise RuntimeError("model not available")

    module.SemanticDetector = unavailable
    monkeypatch.setitem(sys.modules, module.__name__, module)
    evidence = report(projects, use_semantic=True)["evidence"]
    assert evidence["analysis"]["semantic"]["reason"] == "semantic_analysis_failed"
    assert evidence["candidates"][0]["similarity_type"] == "exact"


def test_declared_intent_uses_intract_adapter_and_does_not_inflate_loc(projects, monkeypatch):
    module = types.ModuleType("intract.integrations.redup")

    @dataclass
    class BlockAdapter:
        content: str
        file_path: str
        start_line: int
        end_line: int

    def groups(*, blocks, threshold):
        assert all(b.content and Path(b.file_path).is_absolute() for b in blocks)
        return [
            {
                "similarity": 0.9,
                "evidence": {"contracts": ["scale.value"]},
                "fragments": [
                    {"file_path": b.file_path, "start_line": b.start_line, "end_line": b.end_line}
                    for b in blocks
                ],
            }
        ]

    module.BlockAdapter = BlockAdapter
    module.find_intent_duplicate_groups = groups
    monkeypatch.setitem(sys.modules, module.__name__, module)
    ordinary = report(projects)
    declared = report(projects, use_intent=True)
    assert ordinary["shared_loc_potential"] == declared["shared_loc_potential"]
    assert ordinary["matches"] == declared["matches"]
    candidates = declared["evidence"]["candidates"]
    intent = next(c for c in candidates if c["similarity_type"] == "intent")
    assert intent["intent_evidence"] == "declared"
    assert intent["intent_contracts"] == ["scale.value"]
    assert intent["semantic_equivalence"] == "unknown"
    assert intent["usable_source_evidence"]


def test_legacy_comparison_has_no_fabricated_source_evidence():
    evidence = comparison_to_dict(CrossProjectComparison(Path("/a"), Path("/b")), [])["evidence"]
    assert evidence["sources"] == {}
    assert evidence["candidates"] == []
    assert evidence["quality_winner"] is None


def test_overlap_recommendation_remains_advisory(projects):
    from redup.core.community import detect_communities

    comparison = compare_projects(*projects)
    result = comparison_to_dict(comparison, detect_communities(comparison))
    assert result["recommendation"]["authority"] == "advisory_only"
    assert result["recommendation"]["quality_winner"] is None
    assert result["recommendation"]["compatibility"] == "unknown"


def test_real_intract_inline_declarations(projects):
    pytest.importorskip("intract")
    code = (
        "def scale(value):\n"
        "    # @intract.v1 scope:function intent:scale:value\n"
        "    return value * 2\n"
    )
    for root in projects:
        (root / "code.py").write_text(code)
    evidence = report(projects, use_intent=True)["evidence"]
    assert evidence["analysis"]["declared_intent"]["status"] == "evaluated"
    assert any(c["intent_evidence"] == "declared" for c in evidence["candidates"])


def test_report_limit_also_bounds_evidence_candidates(projects):
    for root in projects:
        (root / "code.py").write_text(FUNCTION + "\n" + FUNCTION.replace("double", "twice"))
    comparison = compare_projects(*projects)
    result = comparison_to_dict(comparison, [], max_matches=1)
    assert len(result["matches"]) == 1
    assert len(result["evidence"]["candidates"]) == 1
    assert result["evidence"]["selection"]["truncated"]


def test_semantic_matches_keep_project_identity_and_inferred_status(projects, monkeypatch):
    from redup.core.comparator import _find_semantic_matches

    blocks = [CodeBlock(str(root / "code.py"), 1, 3, FUNCTION, "double") for root in projects]
    module = types.ModuleType("redup.core.semantic")

    class Detector:
        def __init__(self, **kwargs):
            pass

        def find_semantic_duplicates_fast(self, actual):
            assert actual == blocks
            return [types.SimpleNamespace(block_a=blocks[0], block_b=blocks[1], similarity=0.9)]

    module.SemanticDetector = Detector
    monkeypatch.setitem(sys.modules, module.__name__, module)
    diagnostics = {}
    matches = _find_semantic_matches(
        blocks[:1], blocks[1:], 0.75, str(projects[0]), str(projects[1]), diagnostics=diagnostics
    )
    assert diagnostics["status"] == "evaluated"
    comparison = compare_projects(*projects)
    comparison.matches = matches
    candidate = comparison_to_dict(comparison, [])["evidence"]["candidates"][0]
    assert candidate["intent_evidence"] == "inferred"
    assert candidate["source_a"]["repository"] != candidate["source_b"]["repository"]
    assert candidate["semantic_equivalence"] == "unknown"
