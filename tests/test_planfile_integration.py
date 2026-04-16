"""Tests for planfile integration module."""
from __future__ import annotations

from pathlib import Path

import pytest

from redup.core.models import (
    CodeBlock,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
)

# Skip all tests if planfile is not installed
pytestmark = pytest.mark.skipif(
    pytest.importorskip("planfile", reason="planfile not installed"),
    reason="planfile integration tests require planfile package",
)

from redup.integrations.planfile_integration import (
    DuplicateTask,
    DuplicateTaskExporter,
    TaskConfig,
    export_to_planfile,
)


def create_test_duplication_map() -> DuplicationMap:
    """Create a test duplication map with sample data."""
    blocks = [
        CodeBlock(
            id="test-1",
            file="src/utils.py",
            function_name="process_data",
            line_start=10,
            line_end=20,
            lines_of_code=10,
            hash="abc123",
            content="def process_data(): pass",
            language=".py",
        ),
        CodeBlock(
            id="test-2",
            file="src/helpers.py",
            function_name="process_data",
            line_start=5,
            line_end=15,
            lines_of_code=10,
            hash="abc123",
            content="def process_data(): pass",
            language=".py",
        ),
    ]

    group = DuplicateGroup(
        id="grp-001",
        duplicate_type=DuplicateType.FUNCTION,
        fragments=blocks,
        total_lines=10,
        occurrences=2,
        saved_lines_potential=10,
        normalized_name="process_data",
    )

    return DuplicationMap(
        groups=[group],
        total_duplicate_lines=10,
        duplicate_functions=1,
        duplicate_blocks=0,
    )


class TestDuplicateTaskExporter:
    """Test the DuplicateTaskExporter class."""

    def test_init_default_config(self):
        """Test exporter initializes with default config."""
        exporter = DuplicateTaskExporter()
        assert exporter.config is not None
        assert exporter.config.todo_file == Path("TODO.md")
        assert exporter.config.sync_enabled is False

    def test_init_custom_config(self):
        """Test exporter initializes with custom config."""
        config = TaskConfig(
            todo_file=Path("custom.md"),
            sync_backend="github",
            sync_enabled=True,
        )
        exporter = DuplicateTaskExporter(config)
        assert exporter.config.todo_file == Path("custom.md")
        assert exporter.config.sync_enabled is True

    def test_generate_tasks(self, tmp_path):
        """Test task generation from duplication map."""
        dup_map = create_test_duplication_map()
        exporter = DuplicateTaskExporter()
        exporter.config.todo_file = tmp_path / "TODO.md"

        tasks = exporter._generate_tasks(dup_map)

        assert len(tasks) == 1
        assert tasks[0].title == "Refactor: process_data (2x duplication)"
        assert tasks[0].lines_saved == 10
        assert "src/utils.py" in tasks[0].files
        assert "src/helpers.py" in tasks[0].files

    def test_create_task_difficulty_easy(self):
        """Test task difficulty for single-file duplication."""
        dup_map = create_test_duplication_map()
        exporter = DuplicateTaskExporter()

        # Modify to single file
        dup_map.groups[0].fragments[1].file = "src/utils.py"

        tasks = exporter._generate_tasks(dup_map)
        assert tasks[0].difficulty == "easy"

    def test_create_task_difficulty_hard(self):
        """Test task difficulty for cross-package duplication."""
        dup_map = create_test_duplication_map()
        exporter = DuplicateTaskExporter()

        # Set up cross-package scenario
        dup_map.groups[0].fragments[0].file = "core/utils.py"
        dup_map.groups[0].fragments[1].file = "api/helpers.py"

        tasks = exporter._generate_tasks(dup_map)
        assert tasks[0].difficulty == "hard"

    def test_export_creates_file(self, tmp_path):
        """Test export creates TODO.md file."""
        dup_map = create_test_duplication_map()
        output_file = tmp_path / "TODO.md"

        config = TaskConfig(todo_file=output_file)
        exporter = DuplicateTaskExporter(config)

        result = exporter.export(dup_map)

        assert result == output_file
        assert output_file.exists()
        content = output_file.read_text()
        assert "# TODO - Duplication Refactoring Tasks" in content
        assert "process_data" in content

    def test_render_todo_md_structure(self, tmp_path):
        """Test TODO.md has correct structure."""
        dup_map = create_test_duplication_map()
        exporter = DuplicateTaskExporter()
        exporter.config.todo_file = tmp_path / "TODO.md"

        exporter.export(dup_map)
        content = exporter.config.todo_file.read_text()

        # Check sections exist
        assert "# TODO - Duplication Refactoring Tasks" in content
        assert "Total tasks: 1" in content
        assert "process_data" in content

        # Check priority section
        assert "## MAJOR" in content or "## CRITICAL" in content or "## MINOR" in content

        # Check task details
        assert "- [ ]" in content
        assert "🟢" in content or "🟡" in content or "🔴" in content


class TestExportToPlanfile:
    """Test the export_to_planfile convenience function."""

    def test_export_to_planfile_creates_file(self, tmp_path):
        """Test convenience function creates output file."""
        dup_map = create_test_duplication_map()
        output_file = tmp_path / "refactoring.md"

        result = export_to_planfile(dup_map, output_file)

        assert result == output_file
        assert output_file.exists()

    def test_export_to_planfile_with_backend(self, tmp_path):
        """Test export with sync backend configured."""
        dup_map = create_test_duplication_map()
        output_file = tmp_path / "tasks.md"

        # This should not fail even without actual backend credentials
        result = export_to_planfile(
            dup_map,
            output_file,
            sync_backend="github",
        )

        assert result == output_file


class TestDuplicateTask:
    """Test the DuplicateTask dataclass."""

    def test_task_creation(self):
        """Test task dataclass creation."""
        task = DuplicateTask(
            title="Test Task",
            description="Test description",
            files=["a.py", "b.py"],
            lines_saved=20,
            priority="major",
            difficulty="medium",
        )

        assert task.title == "Test Task"
        assert task.lines_saved == 20
        assert task.difficulty == "medium"
        assert task.task_id is None

    def test_task_with_external_data(self):
        """Test task with external sync data."""
        task = DuplicateTask(
            title="Test Task",
            description="Test",
            files=["a.py"],
            lines_saved=10,
            priority="minor",
            difficulty="easy",
            task_id="GITHUB-123",
            external_url="https://github.com/org/repo/issues/123",
        )

        assert task.task_id == "GITHUB-123"
        assert "github.com" in task.external_url
