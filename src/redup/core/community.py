"""Community detection — find clusters of mutually similar code across projects.

Uses networkx greedy modularity community detection to identify groups of
functions that are strong candidates for extraction into a shared library.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from redup.core.comparator import CrossProjectComparison, CrossProjectMatch


@dataclass
class CodeCommunity:
    """A cluster of similar functions across projects — refactoring candidate."""

    id: int
    members: list[tuple[str, str]] = field(default_factory=list)  # (project, node_key)
    avg_similarity: float = 0.0
    total_loc: int = 0
    extraction_candidate_name: str = ""


def detect_communities(
    comparison: CrossProjectComparison,
    min_similarity: float = 0.70,
) -> list[CodeCommunity]:
    """Build similarity graph and detect communities via networkx.

    Args:
        comparison: Result of ``compare_projects``.
        min_similarity: Minimum edge weight to include.

    Returns:
        Communities sorted by total LOC (descending).

    Raises:
        ImportError: If networkx is not installed.
    """
    try:
        import networkx as nx
    except ImportError:
        raise ImportError(
            "networkx is required for community detection. "
            "Install with: pip install redup[compare]"
        )

    G = nx.Graph()

    for match in comparison.matches:
        if match.similarity < min_similarity:
            continue

        node_a = f"{match.project_a}::{match.file_a}::{match.function_a}"
        node_b = f"{match.project_b}::{match.file_b}::{match.function_b}"

        G.add_node(
            node_a,
            project=match.project_a,
            function=match.function_a,
            loc=match.lines_a[1] - match.lines_a[0],
        )
        G.add_node(
            node_b,
            project=match.project_b,
            function=match.function_b,
            loc=match.lines_b[1] - match.lines_b[0],
        )
        G.add_edge(node_a, node_b, weight=match.similarity)

    if G.number_of_nodes() == 0:
        return []

    # Greedy modularity community detection
    communities_raw = nx.community.greedy_modularity_communities(G, weight="weight")

    communities: list[CodeCommunity] = []
    for i, member_set in enumerate(communities_raw):
        if len(member_set) < 2:
            continue

        members: list[tuple[str, str]] = []
        similarities: list[float] = []
        total_loc = 0
        func_names: list[str] = []

        for node in member_set:
            data = G.nodes[node]
            members.append((data["project"], node))
            total_loc += data.get("loc", 0)
            func_names.append(data["function"])

        for u, v in G.subgraph(member_set).edges:
            similarities.append(G[u][v]["weight"])

        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0

        common_name = _longest_common_prefix(func_names) or f"shared_util_{i}"

        communities.append(CodeCommunity(
            id=i,
            members=members,
            avg_similarity=avg_sim,
            total_loc=total_loc,
            extraction_candidate_name=common_name,
        ))

    return sorted(communities, key=lambda c: c.total_loc, reverse=True)


def _longest_common_prefix(names: list[str]) -> str:
    """Return the longest common prefix of a list of strings."""
    names = [n for n in names if n]
    if not names:
        return ""
    shortest = min(names, key=len)
    for i, c in enumerate(shortest):
        if any(n[i] != c for n in names):
            return shortest[:i]
    return shortest
