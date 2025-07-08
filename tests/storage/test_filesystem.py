"""Tests for filesystem storage layer."""

import tempfile
import shutil
from pathlib import Path
import pytest

from agile_mcp.storage.filesystem import AgileProjectManager


class TestAgileProjectManager:
    """Test cases for AgileProjectManager."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_init_creates_agile_directory_structure(self) -> None:
        """Test that initialization creates the proper .agile directory structure."""
        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        agile_dir = self.project_path / ".agile"
        assert agile_dir.exists()
        assert agile_dir.is_dir()

        # Check subdirectories
        expected_subdirs = ["stories", "sprints", "tasks", "epics", "reports", "archive"]
        for subdir in expected_subdirs:
            subdir_path = agile_dir / subdir
            assert subdir_path.exists(), f"Missing subdirectory: {subdir}"
            assert subdir_path.is_dir(), f"Not a directory: {subdir}"

    def test_init_creates_config_file(self) -> None:
        """Test that initialization creates a config.yml file."""
        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        config_file = self.project_path / ".agile" / "config.yml"
        assert config_file.exists()
        assert config_file.is_file()

    def test_init_skips_if_already_initialized(self) -> None:
        """Test that initialization is idempotent."""
        manager = AgileProjectManager(str(self.project_path))

        # First initialization
        manager.initialize()
        agile_dir = self.project_path / ".agile"
        assert agile_dir.exists()

        # Create a test file to check if it's preserved
        test_file = agile_dir / "test_file.txt"
        test_file.write_text("test content")

        # Second initialization should not overwrite
        manager.initialize()
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_is_initialized_returns_correct_status(self) -> None:
        """Test that is_initialized correctly reports initialization status."""
        manager = AgileProjectManager(str(self.project_path))

        # Before initialization
        assert not manager.is_initialized()

        # After initialization
        manager.initialize()
        assert manager.is_initialized()

    def test_get_agile_dir_returns_correct_path(self) -> None:
        """Test that get_agile_dir returns the correct path."""
        manager = AgileProjectManager(str(self.project_path))
        expected_path = self.project_path / ".agile"

        assert manager.get_agile_dir() == expected_path

    def test_get_subdirectory_paths(self) -> None:
        """Test that subdirectory paths are correctly returned."""
        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Test individual subdirectory getters
        assert manager.get_stories_dir() == self.project_path / ".agile" / "stories"
        assert manager.get_sprints_dir() == self.project_path / ".agile" / "sprints"
        assert manager.get_tasks_dir() == self.project_path / ".agile" / "tasks"
        assert manager.get_epics_dir() == self.project_path / ".agile" / "epics"
        assert manager.get_reports_dir() == self.project_path / ".agile" / "reports"
        assert manager.get_archive_dir() == self.project_path / ".agile" / "archive"

    def test_invalid_project_path_raises_error(self) -> None:
        """Test that invalid project path raises appropriate error."""
        invalid_path = "/nonexistent/path/that/should/not/exist"

        with pytest.raises(ValueError, match="Project path does not exist"):
            AgileProjectManager(invalid_path)

    def test_project_path_must_be_directory(self) -> None:
        """Test that project path must be a directory, not a file."""
        # Create a file instead of directory
        file_path = Path(self.test_dir) / "not_a_directory.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError, match="Project path must be a directory"):
            AgileProjectManager(str(file_path))

    def test_ensure_directory_creates_missing_directories(self) -> None:
        """Test that ensure_directory creates missing directories."""
        manager = AgileProjectManager(str(self.project_path))

        # Test with a nested path that doesn't exist
        test_path = self.project_path / "deep" / "nested" / "path"
        manager._ensure_directory(test_path)

        assert test_path.exists()
        assert test_path.is_dir()

    def test_backup_and_restore_functionality(self) -> None:
        """Test backup and restore functionality for data integrity."""
        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Create some test data
        stories_dir = manager.get_stories_dir()
        test_story_file = stories_dir / "STORY-001.yml"
        test_content = "id: STORY-001\ntitle: Test Story"
        test_story_file.write_text(test_content)

        # Test backup creation
        backup_path = manager.create_backup()
        assert backup_path.exists()
        assert backup_path.is_file()

        # Modify original file
        test_story_file.write_text("modified content")
        assert test_story_file.read_text() == "modified content"

        # Test restore
        manager.restore_backup(backup_path)
        assert test_story_file.read_text() == test_content

    def test_status_folder_migration_on_save(self):
        """Test that files are moved to correct status folder when status changes."""
        from agile_mcp.models.story import UserStory, StoryStatus

        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Create a story in TODO status
        story = UserStory(
            id="STORY-MIGRATE", title="Migration Test", description="Test migration", status=StoryStatus.TODO
        )
        manager.save_story(story)

        # Verify initial location
        todo_path = manager.get_stories_dir() / "todo" / "STORY-MIGRATE.yml"
        assert todo_path.exists()

        # Update status and save
        story.status = StoryStatus.DONE
        manager.save_story(story)

        # Verify file moved to done folder
        done_path = manager.get_stories_dir() / "done" / "STORY-MIGRATE.yml"
        assert done_path.exists()
        assert not todo_path.exists()  # Old file should be gone

    def test_backwards_compatibility_loading(self):
        """Test that files in root directory are still loaded (backwards compatibility)."""
        from agile_mcp.models.story import StoryStatus
        import yaml

        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Manually create a story file in root directory (legacy format)
        stories_dir = manager.get_stories_dir()
        legacy_file = stories_dir / "STORY-LEGACY.yml"

        story_data = {
            "id": "STORY-LEGACY",
            "title": "Legacy Story",
            "description": "Legacy description",
            "status": "todo",
            "priority": "medium",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "tags": [],
        }

        with open(legacy_file, "w") as f:
            yaml.dump(story_data, f)

        # Should be able to load the legacy story
        loaded_story = manager.get_story("STORY-LEGACY")
        assert loaded_story is not None
        assert loaded_story.title == "Legacy Story"
        assert loaded_story.status == StoryStatus.TODO

        # After loading and saving, it should move to status folder
        manager.save_story(loaded_story)

        # Should now be in todo subfolder
        todo_path = stories_dir / "todo" / "STORY-LEGACY.yml"
        assert todo_path.exists()
        assert not legacy_file.exists()  # Legacy file should be gone

    def test_status_mismatch_correction(self):
        """Test that files in wrong status folder are corrected based on content."""
        from agile_mcp.models.story import StoryStatus
        import yaml

        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Create a story file in wrong status folder
        stories_dir = manager.get_stories_dir()
        wrong_folder = stories_dir / "todo"
        wrong_folder.mkdir(exist_ok=True)

        wrong_file = wrong_folder / "STORY-MISMATCH.yml"

        # Create story data with DONE status but place it in TODO folder
        story_data = {
            "id": "STORY-MISMATCH",
            "title": "Mismatched Story",
            "description": "Status mismatch test",
            "status": "done",  # This doesn't match the "todo" folder
            "priority": "medium",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "tags": [],
        }

        with open(wrong_file, "w") as f:
            yaml.dump(story_data, f)

        # Load the story - should auto-correct the location
        loaded_story = manager.get_story("STORY-MISMATCH")
        assert loaded_story is not None
        assert loaded_story.status == StoryStatus.DONE

        # File should have been moved to correct folder
        correct_path = stories_dir / "done" / "STORY-MISMATCH.yml"
        assert correct_path.exists()
        assert not wrong_file.exists()

    def test_list_stories_from_multiple_folders(self):
        """Test that listing stories works across all status folders."""
        from agile_mcp.models.story import UserStory, StoryStatus

        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Create stories with different statuses
        stories = [
            UserStory(id="STORY-TODO", title="TODO Story", description="Test", status=StoryStatus.TODO),
            UserStory(
                id="STORY-PROGRESS", title="In Progress Story", description="Test", status=StoryStatus.IN_PROGRESS
            ),
            UserStory(id="STORY-DONE", title="Done Story", description="Test", status=StoryStatus.DONE),
        ]

        for story in stories:
            manager.save_story(story)

        # List all stories
        all_stories = manager.list_stories()

        assert len(all_stories) == 3
        story_ids = [s.id for s in all_stories]
        assert "STORY-TODO" in story_ids
        assert "STORY-PROGRESS" in story_ids
        assert "STORY-DONE" in story_ids

    def test_task_status_folders(self):
        """Test that task status folders work correctly."""
        from agile_mcp.models.task import Task, TaskStatus

        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Create tasks with different statuses
        tasks = [
            Task(id="TASK-TODO", title="TODO Task", description="Test", status=TaskStatus.TODO),
            Task(id="TASK-PROGRESS", title="In Progress Task", description="Test", status=TaskStatus.IN_PROGRESS),
            Task(id="TASK-DONE", title="Done Task", description="Test", status=TaskStatus.DONE),
        ]

        for task in tasks:
            manager.save_task(task)

        # Verify files are in correct folders
        tasks_dir = manager.get_tasks_dir()
        assert (tasks_dir / "todo" / "TASK-TODO.yml").exists()
        assert (tasks_dir / "in_progress" / "TASK-PROGRESS.yml").exists()
        assert (tasks_dir / "done" / "TASK-DONE.yml").exists()

        # List all tasks
        all_tasks = manager.list_tasks()
        assert len(all_tasks) == 3

    def test_sprint_status_folders(self):
        """Test that sprint status folders work correctly."""
        from agile_mcp.models.sprint import Sprint, SprintStatus

        manager = AgileProjectManager(str(self.project_path))
        manager.initialize()

        # Create sprints with different statuses
        sprints = [
            Sprint(id="SPRINT-PLAN", name="Planning Sprint", status=SprintStatus.PLANNING),
            Sprint(id="SPRINT-ACTIVE", name="Active Sprint", status=SprintStatus.ACTIVE),
            Sprint(id="SPRINT-DONE", name="Completed Sprint", status=SprintStatus.COMPLETED),
        ]

        for sprint in sprints:
            manager.save_sprint(sprint)

        # Verify files are in correct folders
        sprints_dir = manager.get_sprints_dir()
        assert (sprints_dir / "planning" / "SPRINT-PLAN.yml").exists()
        assert (sprints_dir / "active" / "SPRINT-ACTIVE.yml").exists()
        assert (sprints_dir / "completed" / "SPRINT-DONE.yml").exists()

        # List all sprints
        all_sprints = manager.list_sprints()
        assert len(all_sprints) == 3
