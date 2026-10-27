"""Community detection — find clusters of mutually similar code across projects.

Uses networkx greedy modularity community detection when installed, falling back
to pure-Python connected-component clustering so cross-project comparison works
without optional graph dependencies.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from redup.core.comparator import CrossProjectComparison


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
    use_networkx: bool = True,
) -> list[CodeCommunity]:
    """Build similarity graph and detect communities via networkx or BFS fallback.

    Args:
        comparison: Result of ``compare_projects``.
        min_similarity: Minimum edge weight to include.
        use_networkx: Whether to prefer networkx when installed.

    Returns:
        Communities sorted by total LOC (descending).
    """
    nodes: dict[str, dict[str, object]] = {}
    adj: dict[str, dict[str, float]] = {}

    for match in comparison.matches:
        if match.similarity < min_similarity:
            continue

        node_a = f"{match.project_a}::{match.file_a}::{match.function_a}"
        node_b = f"{match.project_b}::{match.file_b}::{match.function_b}"

        nodes[node_a] = {
            "project": match.project_a,
            "function": match.function_a,
            "loc": max(0, match.lines_a[1] - match.lines_a[0] + 1),
        }
        nodes[node_b] = {
            "project": match.project_b,
            "function": match.function_b,
            "loc": max(0, match.lines_b[1] - match.lines_b[0] + 1),
        }
        adj.setdefault(node_a, {})[node_b] = max(
            adj.get(node_a, {}).get(node_b, 0.0), match.similarity
        )
        adj.setdefault(node_b, {})[node_a] = max(
            adj.get(node_b, {}).get(node_a, 0.0), match.similarity
        )

    if not nodes:
        return []

    communities_raw: list[set[str]] | None = None
    if use_networkx:
        try:
            import networkx as nx

            G = nx.Graph()
            for node_id, meta in nodes.items():
                G.add_node(node_id, **meta)
            for u, neighbors in adj.items():
                for v, weight in neighbors.items():
                    if u < v:
                        G.add_edge(u, v, weight=weight)
            communities_raw = [
                set(c) for c in nx.community.greedy_modularity_communities(G, weight="weight")
            ]
        except ImportError:
            communities_raw = None

    if communities_raw is None:
        communities_raw = _connected_components(nodes, adj)

    communities: list[CodeCommunity] = []
    for i, member_set in enumerate(communities_raw):
        if len(member_set) < 2:
            continue

        members: list[tuple[str, str]] = []
        similarities: list[float] = []
        total_loc = 0
        func_names: list[str] = []

        for node in sorted(member_set):
            data = nodes[node]
            members.append((str(data["project"]), node))
            total_loc += int(data.get("loc", 0))
            func_names.append(str(data["function"]))

        for u in member_set:
            for v, weight in adj.get(u, {}).items():
                if u < v and v in member_set:
                    similarities.append(weight)

        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0

        common_name = _longest_common_prefix(func_names) or f"shared_util_{i}"

        communities.append(
            CodeCommunity(
                id=i,
                members=members,
                avg_similarity=avg_sim,
                total_loc=total_loc,
                extraction_candidate_name=common_name,
            )
        )

    return sorted(communities, key=lambda c: c.total_loc, reverse=True)


def _connected_components(
    nodes: dict[str, dict[str, object]],
    adj: dict[str, dict[str, float]],
) -> list[set[str]]:
    """Extract connected components from an undirected adjacency map via BFS."""
    visited: set[str] = set()
    components: list[set[str]] = []
    for start in sorted(nodes):
        if start in visited:
            continue
        comp: set[str] = set()
        queue: deque[str] = deque([start])
        visited.add(start)
        while queue:
            curr = queue.popleft()
            comp.add(curr)
            for nxt in adj.get(curr, {}):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        components.append(comp)
    return components


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
