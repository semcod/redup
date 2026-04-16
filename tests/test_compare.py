"""Tests for the cross-project compare feature (comparator, community, decision)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from redup.core.comparator import (
    CrossProjectComparison,
    CrossProjectMatch,
    compare_projects,
    _find_hash_matches,
)
from redup.core.decision import RefactorDecision, recommend
from redup.core.scanner_models import CodeBlock


# ---------------------------------------------------------------------------
# Fixtures: two tiny on-disk projects with overlapping code
# ---------------------------------------------------------------------------

_SHARED_FUNC = textwrap.dedent("""\
    def validate_email(email: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
        return bool(re.match(pattern, email))
""")

_UNIQUE_A = textwrap.dedent("""\
    def compute_tax(amount: float, rate: float) -> float:
        return round(amount * rate, 2)
""")

_UNIQUE_B = textwrap.dedent("""\
    def format_currency(value: float) -> str:
        return f"${value:,.2f}"
""")


@pytest.fixture()
def twin_projects(tmp_path: Path):
    """Create two projects that share one function."""
    proj_a = tmp_path / "project_a"
    proj_b = tmp_path / "project_b"
    proj_a.mkdir()
    proj_b.mkdir()

    (proj_a / "utils.py").write_text(_SHARED_FUNC + "\n" + _UNIQUE_A, encoding="utf-8")
    (proj_b / "helpers.py").write_text(_SHARED_FUNC + "\n" + _UNIQUE_B, encoding="utf-8")

    return proj_a, proj_b


@pytest.fixture()
def disjoint_projects(tmp_path: Path):
    """Create two projects with zero overlap."""
    proj_a = tmp_path / "alpha"
    proj_b = tmp_path / "beta"
    proj_a.mkdir()
    proj_b.mkdir()

    (proj_a / "a.py").write_text(_UNIQUE_A, encoding="utf-8")
    (proj_b / "b.py").write_text(_UNIQUE_B, encoding="utf-8")

    return proj_a, proj_b


# ---------------------------------------------------------------------------
# Unit tests: _find_hash_matches
# ---------------------------------------------------------------------------

class TestFindHashMatches:
    def test_identical_blocks_detected(self):
        block_a = CodeBlock(file="a/f.py", line_start=1, line_end=4, text=_SHARED_FUNC, function_name="validate_email")
        block_b = CodeBlock(file="b/g.py", line_start=1, line_end=4, text=_SHARED_FUNC, function_name="validate_email")

        matches = _find_hash_matches([block_a], [block_b], "/a", "/b")
        assert len(matches) == 1
        assert matches[0].similarity == 1.0
        assert matches[0].similarity_type == "structural"

    def test_different_blocks_no_match(self):
        block_a = CodeBlock(file="a/f.py", line_start=1, line_end=2, text=_UNIQUE_A, function_name="compute_tax")
        block_b = CodeBlock(file="b/g.py", line_start=1, line_end=2, text=_UNIQUE_B, function_name="format_currency")

        matches = _find_hash_matches([block_a], [block_b], "/a", "/b")
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Integration tests: compare_projects
# ---------------------------------------------------------------------------

class TestCompareProjects:
    def test_shared_function_detected(self, twin_projects):
        proj_a, proj_b = twin_projects
        result = compare_projects(proj_a, proj_b, similarity_threshold=0.75)

        assert isinstance(result, CrossProjectComparison)
        assert result.stats_a["files"] >= 1
        assert result.stats_b["files"] >= 1
        # The shared validate_email function should produce at least one match
        assert result.total_matches >= 1
        structural = [m for m in result.matches if m.similarity_type == "structural"]
        assert len(structural) >= 1

    def test_disjoint_projects_no_matches(self, disjoint_projects):
        proj_a, proj_b = disjoint_projects
        result = compare_projects(proj_a, proj_b, similarity_threshold=0.75)

        assert result.total_matches == 0


# ---------------------------------------------------------------------------
# Unit tests: community detection
# ---------------------------------------------------------------------------

class TestCommunityDetection:
    def _make_comparison(self, n_matches: int = 5) -> CrossProjectComparison:
        matches = []
        for i in range(n_matches):
            matches.append(CrossProjectMatch(
                project_a="/a", project_b="/b",
                file_a=f"a/f{i}.py", file_b=f"b/g{i}.py",
                function_a=f"validate_{i}", function_b=f"validate_{i}",
                similarity=0.90,
                similarity_type="structural",
                lines_a=(1, 10), lines_b=(1, 10),
            ))
        return CrossProjectComparison(
            project_a=Path("/a"), project_b=Path("/b"),
            matches=matches,
            stats_a={"files": 10, "lines": 500},
            stats_b={"files": 8, "lines": 400},
        )

    def test_detect_communities_requires_networkx(self):
        try:
            import networkx  # noqa: F401
        except ImportError:
            pytest.skip("networkx not installed")

        from redup.core.community import detect_communities
        comparison = self._make_comparison()
        communities = detect_communities(comparison, min_similarity=0.70)
        assert isinstance(communities, list)

    def test_no_matches_yields_no_communities(self):
        try:
            import networkx  # noqa: F401
        except ImportError:
            pytest.skip("networkx not installed")

        from redup.core.community import detect_communities
        comparison = CrossProjectComparison(
            project_a=Path("/a"), project_b=Path("/b"),
            stats_a={"files": 1, "lines": 10},
            stats_b={"files": 1, "lines": 10},
        )
        communities = detect_communities(comparison)
        assert communities == []


# ---------------------------------------------------------------------------
# Unit tests: decision engine
# ---------------------------------------------------------------------------

class TestDecision:
    def test_keep_separate_when_no_overlap(self):
        comparison = CrossProjectComparison(
            project_a=Path("/a"), project_b=Path("/b"),
            stats_a={"files": 10, "lines": 1000},
            stats_b={"files": 10, "lines": 1000},
        )
        rec = recommend(comparison, communities=[])
        assert rec.decision == RefactorDecision.KEEP_SEPARATE
        assert rec.confidence >= 0.8

    def test_merge_when_high_overlap(self):
        from redup.core.community import CodeCommunity
        comparison = CrossProjectComparison(
            project_a=Path("/a"), project_b=Path("/b"),
            stats_a={"files": 10, "lines": 500},
            stats_b={"files": 10, "lines": 500},
        )
        big_community = CodeCommunity(
            id=0, members=[("/a", "x"), ("/b", "y")],
            avg_similarity=0.95, total_loc=700,
            extraction_candidate_name="shared",
        )
        rec = recommend(comparison, communities=[big_community])
        assert rec.decision == RefactorDecision.MERGE_PROJECTS

    def test_extract_shared_lib_moderate_overlap(self):
        from redup.core.community import CodeCommunity
        comparison = CrossProjectComparison(
            project_a=Path("/a"), project_b=Path("/b"),
            stats_a={"files": 10, "lines": 500},
            stats_b={"files": 10, "lines": 500},
        )
        community = CodeCommunity(
            id=0, members=[("/a", "x"), ("/b", "y")],
            avg_similarity=0.85, total_loc=250,
            extraction_candidate_name="validate_",
        )
        rec = recommend(comparison, communities=[community])
        assert rec.decision == RefactorDecision.EXTRACT_SHARED_LIB
