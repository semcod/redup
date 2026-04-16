"""Integration with planfile for creating tasks from duplications.

This module provides functionality to export duplication findings as tasks
to TODO.md with support for GitHub, GitLab, and Jira synchronization.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redup.core.models import DuplicationMap, DuplicateGroup


@dataclass
class TaskConfig:
    """Configuration for task export."""

    todo_file: Path = Path("TODO.md")
    sync_backend: str | None = None  # "github", "gitlab", "jira"
    sync_enabled: bool = False
    milestone: str | None = None
    labels: list[str] = field(default_factory=lambda: ["refactoring", "duplication"])
    priority_map: dict[str, str] = field(default_factory=lambda: {
        "HIGH": "critical",
        "MEDIUM": "major",
        "LOW": "minor",
    })


@dataclass
class DuplicateTask:
    """Represents a task created from a duplicate group."""

    title: str
    description: str
    files: list[str]
    lines_saved: int
    priority: str
    difficulty: str  # "easy", "medium", "hard"
    task_id: str | None = None
    external_url: str | None = None


class DuplicateTaskExporter:
    """Export duplicate groups as tasks to planfile/TODO.md."""

    def __init__(self, config: TaskConfig | None = None):
        self.config = config or TaskConfig()
        self.tasks: list[DuplicateTask] = []

    def export(
        self,
        dup_map: DuplicationMap,
        output_file: Path | None = None,
    ) -> Path:
        """Export duplications to TODO.md format.

        Args:
            dup_map: The duplication map from analysis
            output_file: Optional custom output path (defaults to config.todo_file)

        Returns:
            Path to the created TODO.md file
        """
        todo_file = output_file or self.config.todo_file

        # Generate tasks from duplications
        self.tasks = self._generate_tasks(dup_map)

        # Write TODO.md
        content = self._render_todo_md()
        todo_file.write_text(content, encoding="utf-8")

        # Sync with external backend if configured
        if self.config.sync_enabled and self.config.sync_backend:
            self._sync_to_backend()

        return todo_file

    def _generate_tasks(self, dup_map: DuplicationMap) -> list[DuplicateTask]:
        """Convert duplicate groups to tasks."""
        tasks: list[DuplicateTask] = []

        for group in dup_map.sorted_by_impact():
            if group.saved_lines_potential == 0:
                continue

            task = self._create_task_from_group(group)
            tasks.append(task)

        return tasks

    def _create_task_from_group(self, group: DuplicateGroup) -> DuplicateTask:
        """Create a single task from a duplicate group."""
        # Determine function/block name
        if group.normalized_name:
            name = group.normalized_name
        elif group.fragments and group.fragments[0].function_name:
            name = group.fragments[0].function_name
        else:
            name = f"block_{group.id[:8]}"

        # Collect unique files
        files = sorted({f.file for f in group.fragments})

        # Determine difficulty based on complexity
        files_count = len(files)
        packages = {f.split(os.sep)[0] for f in files if os.sep in f}

        if files_count == 1:
            difficulty = "easy"
        elif len(packages) > 2 or group.total_lines > 50:
            difficulty = "hard"
        else:
            difficulty = "medium"

        # Determine priority based on impact
        if group.saved_lines_potential > 30:
            priority = "critical"
        elif group.saved_lines_potential > 15:
            priority = "major"
        else:
            priority = "minor"

        # Build description
        description = self._build_description(group, files, packages)

        return DuplicateTask(
            title=f"Refactor: {name} ({group.occurrences}x duplication)",
            description=description,
            files=files,
            lines_saved=group.saved_lines_potential,
            priority=priority,
            difficulty=difficulty,
        )

    def _build_description(
        self,
        group: DuplicateGroup,
        files: list[str],
        packages: set[str],
    ) -> str:
        """Build task description with refactoring details."""
        lines: list[str] = []

        lines.append(f"## Duplication Analysis")
        lines.append(f"")
        lines.append(f"- **Occurrences**: {group.occurrences}")
        lines.append(f"- **Lines per block**: {group.total_lines}")
        lines.append(f"- **Potential savings**: {group.saved_lines_potential} lines")
        lines.append(f"- **Files affected**: {len(files)}")
        lines.append(f"- **Packages**: {', '.join(packages) if packages else 'single package'}")
        lines.append(f"")

        lines.append(f"### Files")
        for f in files[:10]:  # Limit to 10 files
            lines.append(f"- `{f}`")
        if len(files) > 10:
            lines.append(f"- ... and {len(files) - 10} more files")
        lines.append(f"")

        lines.append(f"### Suggested Action")
        if len(packages) > 2:
            lines.append(f"Extract to shared library due to cross-package usage.")
        elif group.total_lines > 50:
            lines.append(f"Consider extracting to a new module.")
        elif group.fragments[0].function_name:
            lines.append(f"Extract function to a shared utility module.")
        else:
            lines.append(f"Extract code block to eliminate duplication.")

        return "\n".join(lines)

    def _render_todo_md(self) -> str:
        """Render tasks in TODO.md format."""
        lines: list[str] = []

        # Header
        lines.append("# TODO - Duplication Refactoring Tasks")
        lines.append(f"")
        lines.append(f"Generated by [redup](https://github.com/semcod/redup)")
        lines.append(f"Total tasks: {len(self.tasks)}")
        lines.append(f"Total potential savings: {sum(t.lines_saved for t in self.tasks)} lines")
        lines.append(f"")

        # Group by priority
        by_priority: dict[str, list[DuplicateTask]] = {
            "critical": [],
            "major": [],
            "minor": [],
        }
        for task in self.tasks:
            by_priority.setdefault(task.priority, []).append(task)

        # Render each priority section
        for priority in ["critical", "major", "minor"]:
            tasks = by_priority.get(priority, [])
            if not tasks:
                continue

            lines.append(f"## {priority.upper()} ({len(tasks)} tasks)")
            lines.append(f"")

            for i, task in enumerate(tasks, 1):
                checkbox = "- [ ]" if task.task_id is None else f"- [x]"
                difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(
                    task.difficulty, "⚪"
                )

                lines.append(f"{checkbox} **{task.title}** {difficulty_emoji}")
                lines.append(f"   Priority: {task.priority} | Savings: {task.lines_saved}L")

                if task.external_url:
                    lines.append(f"   External: [{task.task_id}]({task.external_url})")

                # Add expandable description
                lines.append(f"   <details>")
                lines.append(f"   <summary>Details</summary>")
                for desc_line in task.description.split("\n"):
                    lines.append(f"   {desc_line}")
                lines.append(f"   </details>")
                lines.append(f"")

        # Add export section for planfile integration
        lines.append(f"## Planfile Export Configuration")
        lines.append(f"")
        lines.append(f"```yaml")
        lines.append(f"# Add to your planfile.yaml to sync these tasks:")
        lines.append(f"tasks:")
        for task in self.tasks[:5]:  # Show first 5 as examples
            safe_id = re.sub(r"[^a-z0-9_-]", "_", task.title.lower())[:40]
            lines.append(f"  - id: {safe_id}")
            lines.append(f"    title: {task.title}")
            lines.append(f"    priority: {task.priority}")
            lines.append(f"    labels: {self.config.labels}")
            lines.append(f"    description: |")
            for desc_line in task.description.split("\n")[:3]:
                lines.append(f"      {desc_line}")
        lines.append(f"```")

        return "\n".join(lines)

    def _sync_to_backend(self) -> None:
        """Sync tasks to external backend (GitHub/GitLab/Jira)."""
        try:
            from planfile import PlanfileAPI

            api = PlanfileAPI()

            for task in self.tasks:
                if task.task_id:  # Already synced
                    continue

                # Create ticket via planfile
                result = api.create_task(
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    labels=self.config.labels,
                    milestone=self.config.milestone,
                )

                if result:
                    task.task_id = result.get("id")
                    task.external_url = result.get("url")

        except ImportError:
            # planfile not installed, skip sync
            pass
        except Exception:
            # Sync failed but don't break export
            pass


def export_to_planfile(
    dup_map: DuplicationMap,
    output_file: str | Path = "TODO.md",
    sync_backend: str | None = None,
) -> Path:
    """Convenience function to export duplications to TODO.md.

    Args:
        dup_map: The duplication analysis results
        output_file: Path to output TODO.md (default: TODO.md)
        sync_backend: Optional backend to sync with ("github", "gitlab", "jira")

    Returns:
        Path to the generated TODO.md file

    Example:
        >>> from redup import analyze
        >>> from redup.integrations import export_to_planfile
        >>> result = analyze("./my-project")
        >>> export_to_planfile(result, "refactoring-tasks.md", sync_backend="github")
        PosixPath('refactoring-tasks.md')
    """
    config = TaskConfig(
        todo_file=Path(output_file),
        sync_backend=sync_backend,
        sync_enabled=sync_backend is not None,
    )

    exporter = DuplicateTaskExporter(config)
    return exporter.export(dup_map)
