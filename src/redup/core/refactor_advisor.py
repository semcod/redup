"""LLM-powered refactoring advisor using litellm.

Builds a compact structured prompt from CrossProjectComparison data
and generates an actionable refactoring TODO list via any LLM backend.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RefactorTask:
    """A single refactoring action item."""

    priority: str  # "high" | "medium" | "low"
    action: str  # short action title
    description: str  # what to do
    files_a: list[str] = field(default_factory=list)
    files_b: list[str] = field(default_factory=list)
    estimated_loc_saved: int = 0
    difficulty: str = "medium"  # "easy" | "medium" | "hard"


@dataclass
class RefactorPlan:
    """Complete LLM-generated refactoring plan."""

    tasks: list[RefactorTask] = field(default_factory=list)
    summary: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: float = 0.0
    raw_response: str = ""


def _load_env(env_path: Path | None = None) -> None:
    """Load .env file into os.environ."""
    try:
        from dotenv import load_dotenv
        if env_path and env_path.exists():
            load_dotenv(env_path, override=True)
        else:
            cwd_env = Path.cwd() / ".env"
            if cwd_env.exists():
                load_dotenv(cwd_env, override=True)
    except ImportError:
        pass


def _get_model(model_override: str | None = None) -> str:
    """Resolve the LLM model name from override → env → default."""
    if model_override:
        return model_override
    return os.getenv("LLM_MODEL", "openrouter/x-ai/grok-code-fast-1")


def _resolve_stats(report: dict) -> tuple[dict, dict]:
    """Extract project stats, supporting both compact and legacy formats."""
    stats = report.get("stats", {})
    stats_a = stats.get("a") or report.get("stats_a", {})
    stats_b = stats.get("b") or report.get("stats_b", {})
    return stats_a, stats_b


def _normalize_match(m: dict) -> dict:
    """Normalize a single match from compact or legacy format."""
    loc = m.get("loc")
    if loc is None and "lines_a" in m:
        loc = max(
            m["lines_a"][1] - m["lines_a"][0],
            m["lines_b"][1] - m["lines_b"][0],
        )
    else:
        loc = loc or 0

    return {
        "func_a": m.get("func_a") or m.get("function_a", ""),
        "func_b": m.get("func_b") or m.get("function_b", ""),
        "file_a": m.get("file_a", ""),
        "file_b": m.get("file_b", ""),
        "similarity": m.get("similarity", 1.0),
        "type": m.get("type") or m.get("similarity_type", "structural"),
        "loc": loc,
    }


def _build_match_list(report: dict, limit: int = 30) -> list[dict]:
    """Build, sort, and limit match list from report."""
    raw_matches = report.get("matches", [])
    match_list = [_normalize_match(m) for m in raw_matches]
    match_list.sort(key=lambda x: x["loc"], reverse=True)
    return match_list[:limit]


def _format_communities(communities: list[dict]) -> str:
    """Format communities section for prompt."""
    if not communities:
        return ""

    lines = ["\n## Detected Code Communities (clusters of related duplicates)\n"]
    for c in communities[:10]:
        name = c.get("name") or c.get("extraction_candidate_name", "?")
        loc = c.get("loc") or c.get("total_loc", 0)
        sim = c.get("similarity") or c.get("avg_similarity", 0)
        members = c.get("members", [])
        lines.append(
            f"- **{name}**: {loc} LOC, "
            f"{len(members)} members, avg sim={sim:.2f}\n"
        )
    return "".join(lines)


def _format_matches_section(matches: list[dict]) -> str:
    """Format the matches section for prompt."""
    lines = []
    for i, m in enumerate(matches, 1):
        lines.append(
            f"{i}. `{m['func_a']}` (A:{m['file_a']}, {m['loc']}L) "
            f"↔ `{m['func_b']}` (B:{m['file_b']}) "
            f"— {m['type']} sim={m['similarity']:.2f}\n"
        )
    return "".join(lines)


def _build_prompt(report: dict) -> str:
    """Build a compact prompt from comparison report data.

    Performance-optimised: sends only structured metadata, not raw code.
    Supports both compact (new) and verbose (legacy) report formats.
    """
    stats_a, stats_b = _resolve_stats(report)
    top_matches = _build_match_list(report)
    communities = report.get("communities", [])
    rec = report.get("recommendation", {})
    overlap = rec.get("overlap_pct") or rec.get("overlap_percent", 0)

    prompt = f"""You are a senior software architect. Analyze this cross-project code comparison
and produce an actionable refactoring TODO list.

## Project Comparison Summary
- **Project A**: {report['project_a']} ({stats_a.get('files', '?')} files, {stats_a.get('lines', '?')} lines)
- **Project B**: {report['project_b']} ({stats_b.get('files', '?')} files, {stats_b.get('lines', '?')} lines)
- **Cross matches**: {report['total_matches']}
- **Shared LOC potential**: {report['shared_loc_potential']}
- **Recommendation**: {rec.get('decision', 'N/A')} (confidence: {rec.get('confidence', 0):.0%})
- **Overlap**: {overlap:.1%}

## Top Duplicate Matches (function pairs found in both projects)
"""
    prompt += _format_matches_section(top_matches)
    prompt += _format_communities(communities)
    prompt += _get_prompt_instructions()

    return prompt


def _get_prompt_instructions() -> str:
    """Return the instructions section of the prompt."""
    return """
## Instructions
Generate a JSON array of refactoring tasks. Each task:
```json
{
  "priority": "high|medium|low",
  "action": "short title (max 60 chars)",
  "description": "concrete steps, which files to change, what to extract",
  "files_a": ["list of files in project A involved"],
  "files_b": ["list of files in project B involved"],
  "estimated_loc_saved": 123,
  "difficulty": "easy|medium|hard"
}
```

Rules:
1. Group related duplicates into single tasks (don't create one task per match)
2. Prioritize by LOC saved × difficulty trade-off
3. For identical functions (sim=1.0): recommend extracting to a shared package
4. For near-duplicates (sim<1.0): recommend unifying the API, noting differences
5. Include a "summary" field at the top level with 2-3 sentence overview
6. Be specific about file paths and function names
7. Maximum 15 tasks, minimum 3

Return ONLY valid JSON:
```json
{
  "summary": "...",
  "tasks": [...]
}
```"""


def generate_refactor_plan(
    report: dict,
    env_path: Path | None = None,
    model: str | None = None,
) -> RefactorPlan:
    """Generate an LLM-powered refactoring plan from comparison report.

    Args:
        report: JSON report dict from ``_build_json_report``.
        env_path: Path to .env file with API keys.
        model: LLM model override (default: from LLM_MODEL env var).

    Returns:
        RefactorPlan with parsed tasks.

    Raises:
        ImportError: If litellm is not installed.
        RuntimeError: If LLM call fails.
    """
    try:
        import litellm
    except ImportError:
        raise ImportError(
            "litellm is required for LLM-powered refactoring plans. "
            "Install with: pip install redup[llm]"
        )

    _load_env(env_path)
    resolved_model = _get_model(model)
    prompt = _build_prompt(report)

    start = time.monotonic()
    try:
        response = litellm.completion(
            model=resolved_model,
            messages=[
                {"role": "system", "content": "You are a code refactoring expert. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e

    duration_ms = (time.monotonic() - start) * 1000

    raw = response.choices[0].message.content or ""
    usage = response.usage

    plan = RefactorPlan(
        model=resolved_model,
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        duration_ms=duration_ms,
        raw_response=raw,
    )

    # Parse JSON from response (handle markdown code fences)
    plan.tasks, plan.summary = _parse_llm_response(raw)

    return plan


def _parse_llm_response(raw: str) -> tuple[list[RefactorTask], str]:
    """Parse LLM response into structured tasks."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                return [], f"Failed to parse LLM response. Raw:\n{raw[:500]}"
        else:
            return [], f"No JSON found in LLM response. Raw:\n{raw[:500]}"

    summary = data.get("summary", "")
    tasks: list[RefactorTask] = []

    for t in data.get("tasks", []):
        tasks.append(RefactorTask(
            priority=t.get("priority", "medium"),
            action=t.get("action", ""),
            description=t.get("description", ""),
            files_a=t.get("files_a", []),
            files_b=t.get("files_b", []),
            estimated_loc_saved=t.get("estimated_loc_saved", 0),
            difficulty=t.get("difficulty", "medium"),
        ))

    return tasks, summary


def format_plan_markdown(plan: RefactorPlan) -> str:
    """Format a RefactorPlan as a markdown TODO list."""
    lines: list[str] = []
    lines.append("# Refactoring Plan")
    lines.append("")
    lines.append(f"> {plan.summary}")
    lines.append("")
    lines.append(f"*Generated by `{plan.model}` in {plan.duration_ms:.0f}ms "
                 f"({plan.prompt_tokens}→{plan.completion_tokens} tokens)*")
    lines.append("")

    # Group by priority
    for prio in ("high", "medium", "low"):
        prio_tasks = [t for t in plan.tasks if t.priority == prio]
        if not prio_tasks:
            continue

        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[prio]
        lines.append(f"## {emoji} {prio.upper()} Priority")
        lines.append("")

        for i, t in enumerate(prio_tasks, 1):
            lines.append(f"### {i}. {t.action}")
            lines.append(f"- **Difficulty**: {t.difficulty}")
            lines.append(f"- **LOC saved**: ~{t.estimated_loc_saved}")
            lines.append(f"- {t.description}")
            if t.files_a:
                lines.append(f"- **Project A files**: {', '.join(t.files_a[:5])}")
            if t.files_b:
                lines.append(f"- **Project B files**: {', '.join(t.files_b[:5])}")
            lines.append("")

    return "\n".join(lines)


def format_plan_json(plan: RefactorPlan) -> dict:
    """Format a RefactorPlan as a JSON-serialisable dict."""
    return {
        "summary": plan.summary,
        "model": plan.model,
        "prompt_tokens": plan.prompt_tokens,
        "completion_tokens": plan.completion_tokens,
        "duration_ms": plan.duration_ms,
        "tasks": [
            {
                "priority": t.priority,
                "action": t.action,
                "description": t.description,
                "files_a": t.files_a,
                "files_b": t.files_b,
                "estimated_loc_saved": t.estimated_loc_saved,
                "difficulty": t.difficulty,
            }
            for t in plan.tasks
        ],
    }
