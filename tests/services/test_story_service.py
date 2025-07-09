"""Tests for StoryService."""

import tempfile
import shutil
from pathlib import Path
import pytest
from datetime import datetime

from agile_mcp.services.story_service import StoryService
from agile_mcp.models.story import StoryStatus, Priority
from agile_mcp.storage.filesystem import AgileProjectManager


class TestStoryService:
    """Test cases for StoryService."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

        # Initialize project
        self.project_manager = AgileProjectManager(str(self.project_path))
        self.project_manager.initialize()

        # Create story service
        self.story_service = StoryService(self.project_manager)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_create_story_with_minimal_data(self) -> None:
        """Test creating a story with minimal required data."""
        story = self.story_service.create_story(
            name="As a user, I want to login", description="User authentication functionality"
        )

        assert story.name == "As a user, I want to login"
        assert story.description == "User authentication functionality"
        assert story.status == StoryStatus.TODO
        assert story.priority == Priority.MEDIUM
        assert story.points is None
        assert story.sprint_id is None
        assert story.id.startswith("STORY-")
        assert isinstance(story.created_at, datetime)

    def test_create_story_with_all_data(self) -> None:
        """Test creating a story with all optional data."""
        story = self.story_service.create_story(
            name="As a user, I want to logout",
            description="User logout functionality",
            priority=Priority.HIGH,
            points=5,
            tags=["auth", "security"],
        )

        assert story.name == "As a user, I want to logout"
        assert story.description == "User logout functionality"
        assert story.priority == Priority.HIGH
        assert story.points == 5
        assert story.tags == ["auth", "security"]

    def test_create_story_auto_generates_id(self) -> None:
        """Test that story creation auto-generates unique IDs."""
        story1 = self.story_service.create_story("name 1", "Description 1")
        story2 = self.story_service.create_story("name 2", "Description 2")

        assert story1.id != story2.id
        assert story1.id.startswith("STORY-")
        assert story2.id.startswith("STORY-")

    def test_create_story_persists_to_filesystem(self) -> None:
        """Test that created stories are persisted to the filesystem."""
        story = self.story_service.create_story(name="Test persistence", description="Test description")

        # Check that file exists in the correct status subfolder
        story_file = self.project_manager.get_stories_dir() / story.status.value / f"{story.id}.yml"
        assert story_file.exists()

        # Verify file content can be loaded
        loaded_story = self.story_service.get_story(story.id)
        assert loaded_story is not None
        assert loaded_story.name == story.name
        assert loaded_story.description == story.description

    def test_get_story_returns_existing_story(self) -> None:
        """Test retrieving an existing story by ID."""
        # Create a story
        original_story = self.story_service.create_story(
            name="Test story", description="Test description", priority=Priority.HIGH
        )

        # Retrieve it
        retrieved_story = self.story_service.get_story(original_story.id)

        assert retrieved_story is not None
        assert retrieved_story.id == original_story.id
        assert retrieved_story.name == original_story.name
        assert retrieved_story.description == original_story.description
        assert retrieved_story.priority == original_story.priority

    def test_get_story_returns_none_for_nonexistent_id(self) -> None:
        """Test that getting a non-existent story returns None."""
        result = self.story_service.get_story("STORY-NONEXISTENT")
        assert result is None

    def test_update_story_modifies_existing_story(self) -> None:
        """Test updating an existing story."""
        # Create a story
        story = self.story_service.create_story(name="Original name", description="Original description")

        # Update it
        updated_story = self.story_service.update_story(
            story.id, name="Updated name", description="Updated description", priority=Priority.HIGH, points=8
        )

        assert updated_story is not None
        assert updated_story.id == story.id
        assert updated_story.name == "Updated name"
        assert updated_story.description == "Updated description"
        assert updated_story.priority == Priority.HIGH
        assert updated_story.points == 8

    def test_update_story_persists_changes(self) -> None:
        """Test that story updates are persisted to filesystem."""
        # Create a story
        story = self.story_service.create_story("Original", "Original")

        # Update it
        self.story_service.update_story(story.id, name="Updated", description="Updated")

        # Retrieve it again
        retrieved_story = self.story_service.get_story(story.id)
        assert retrieved_story is not None
        assert retrieved_story.name == "Updated"
        assert retrieved_story.description == "Updated"

    def test_update_nonexistent_story_returns_none(self) -> None:
        """Test that updating a non-existent story returns None."""
        result = self.story_service.update_story("STORY-NONEXISTENT", name="Updated name")
        assert result is None

    def test_delete_story_removes_story(self) -> None:
        """Test deleting a story removes it from storage."""
        # Create a story
        story = self.story_service.create_story("To delete", "Description")

        # Verify it exists
        assert self.story_service.get_story(story.id) is not None

        # Delete it
        success = self.story_service.delete_story(story.id)
        assert success is True

        # Verify it no longer exists
        assert self.story_service.get_story(story.id) is None

    def test_delete_nonexistent_story_returns_false(self) -> None:
        """Test that deleting a non-existent story returns False."""
        result = self.story_service.delete_story("STORY-NONEXISTENT")
        assert result is False

    def test_list_stories_returns_all_stories(self) -> None:
        """Test listing all stories."""
        # Create multiple stories
        story1 = self.story_service.create_story("Story 1", "Description 1")
        story2 = self.story_service.create_story("Story 2", "Description 2", priority=Priority.HIGH)
        story3 = self.story_service.create_story("Story 3", "Description 3", status=StoryStatus.DONE)

        # List all stories
        stories = self.story_service.list_stories()

        assert len(stories) == 3
        story_ids = [s.id for s in stories]
        assert story1.id in story_ids
        assert story2.id in story_ids
        assert story3.id in story_ids

    def test_list_stories_with_status_filter(self) -> None:
        """Test listing stories filtered by status."""
        # Create stories with different statuses
        story1 = self.story_service.create_story("Story 1", "Description 1")  # TODO by default
        story2 = self.story_service.create_story("Story 2", "Description 2")
        self.story_service.update_story(story2.id, status=StoryStatus.IN_PROGRESS)
        story3 = self.story_service.create_story("Story 3", "Description 3")
        self.story_service.update_story(story3.id, status=StoryStatus.DONE)

        # Filter by status
        todo_stories = self.story_service.list_stories(status=StoryStatus.TODO)
        in_progress_stories = self.story_service.list_stories(status=StoryStatus.IN_PROGRESS)
        done_stories = self.story_service.list_stories(status=StoryStatus.DONE)

        assert len(todo_stories) == 1
        assert todo_stories[0].id == story1.id

        assert len(in_progress_stories) == 1
        assert in_progress_stories[0].id == story2.id

        assert len(done_stories) == 1
        assert done_stories[0].id == story3.id

    def test_list_stories_with_priority_filter(self) -> None:
        """Test listing stories filtered by priority."""
        # Create stories with different priorities
        story1 = self.story_service.create_story("Story 1", "Description 1", priority=Priority.LOW)
        story2 = self.story_service.create_story("Story 2", "Description 2", priority=Priority.HIGH)
        story3 = self.story_service.create_story("Story 3", "Description 3", priority=Priority.HIGH)

        # Filter by priority
        high_priority_stories = self.story_service.list_stories(priority=Priority.HIGH)
        low_priority_stories = self.story_service.list_stories(priority=Priority.LOW)

        assert len(high_priority_stories) == 2
        high_priority_ids = [s.id for s in high_priority_stories]
        assert story2.id in high_priority_ids
        assert story3.id in high_priority_ids

        assert len(low_priority_stories) == 1
        assert low_priority_stories[0].id == story1.id

    def test_list_stories_with_sprint_filter(self) -> None:
        """Test listing stories filtered by sprint ID."""
        # Create stories with different sprint assignments
        story1 = self.story_service.create_story("Story 1", "Description 1")
        story2 = self.story_service.create_story("Story 2", "Description 2")
        self.story_service.update_story(story2.id, sprint_id="SPRINT-001")
        story3 = self.story_service.create_story("Story 3", "Description 3")
        self.story_service.update_story(story3.id, sprint_id="SPRINT-001")

        # Filter by sprint
        sprint_stories = self.story_service.list_stories(sprint_id="SPRINT-001")
        no_sprint_stories = self.story_service.list_stories(_filter_no_sprint=True)

        assert len(sprint_stories) == 2
        sprint_story_ids = [s.id for s in sprint_stories]
        assert story2.id in sprint_story_ids
        assert story3.id in sprint_story_ids

        assert len(no_sprint_stories) == 1
        assert no_sprint_stories[0].id == story1.id

    def test_validate_story_points_fibonacci_only(self) -> None:
        """Test that story points validation only allows Fibonacci numbers."""
        # Valid Fibonacci numbers should work
        valid_points = [1, 2, 3, 5, 8, 13, 21]
        for points in valid_points:
            story = self.story_service.create_story(f"Story with {points} points", "Description", points=points)
            assert story.points == points

        # Invalid numbers should raise ValueError
        invalid_points = [4, 6, 7, 9, 10, 11, 12, 14, 15]
        for points in invalid_points:
            with pytest.raises(ValueError, match="Story points must be a Fibonacci number"):
                self.story_service.create_story("Invalid story", "Description", points=points)
