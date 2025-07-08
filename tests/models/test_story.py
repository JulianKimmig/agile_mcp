"""Tests for UserStory model."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from agile_mcp.models.story import UserStory, StoryStatus, Priority


class TestStoryStatus:
    """Test cases for StoryStatus enum."""

    def test_story_status_values(self) -> None:
        """Test that all story status values are correct."""
        assert StoryStatus.TODO == "todo"
        assert StoryStatus.IN_PROGRESS == "in_progress"
        assert StoryStatus.IN_REVIEW == "in_review"
        assert StoryStatus.DONE == "done"
        assert StoryStatus.BLOCKED == "blocked"

    def test_story_status_membership(self) -> None:
        """Test membership in StoryStatus enum."""
        valid_statuses = ["todo", "in_progress", "in_review", "done", "blocked"]
        for status in valid_statuses:
            assert status in [s.value for s in StoryStatus]


class TestPriority:
    """Test cases for Priority enum."""

    def test_priority_values(self) -> None:
        """Test that all priority values are correct."""
        assert Priority.CRITICAL == "critical"
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"

    def test_priority_membership(self) -> None:
        """Test membership in Priority enum."""
        valid_priorities = ["critical", "high", "medium", "low"]
        for priority in valid_priorities:
            assert priority in [p.value for p in Priority]


class TestUserStory:
    """Test cases for UserStory model."""

    def test_create_user_story_with_required_fields(self) -> None:
        """Test creating a UserStory with only required fields."""
        story = UserStory(
            id="STORY-001", title="As a user, I want to login", description="User authentication functionality"
        )

        assert story.id == "STORY-001"
        assert story.title == "As a user, I want to login"
        assert story.description == "User authentication functionality"
        assert story.status == StoryStatus.TODO
        assert story.priority == Priority.MEDIUM
        assert story.points is None
        assert story.sprint_id is None
        assert isinstance(story.created_at, datetime)
        assert isinstance(story.updated_at, datetime)

    def test_create_user_story_with_all_fields(self) -> None:
        """Test creating a UserStory with all fields."""
        story = UserStory(
            id="STORY-002",
            title="As a user, I want to logout",
            description="User logout functionality",
            status=StoryStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            points=5,
            sprint_id="SPRINT-001",
            tags=["auth", "security"],
        )

        assert story.id == "STORY-002"
        assert story.title == "As a user, I want to logout"
        assert story.description == "User logout functionality"
        assert story.status == StoryStatus.IN_PROGRESS
        assert story.priority == Priority.HIGH
        assert story.points == 5
        assert story.sprint_id == "SPRINT-001"
        assert story.tags == ["auth", "security"]

    def test_user_story_requires_id(self) -> None:
        """Test that UserStory requires an ID."""
        with pytest.raises(ValidationError) as exc_info:
            UserStory(title="Test story", description="Test description")

        assert "id" in str(exc_info.value)

    def test_user_story_requires_title(self) -> None:
        """Test that UserStory requires a title."""
        with pytest.raises(ValidationError) as exc_info:
            UserStory(id="STORY-003", description="Test description")

        assert "title" in str(exc_info.value)

    def test_user_story_requires_description(self) -> None:
        """Test that UserStory requires a description."""
        with pytest.raises(ValidationError) as exc_info:
            UserStory(id="STORY-004", title="Test story")

        assert "description" in str(exc_info.value)

    def test_user_story_status_validation(self) -> None:
        """Test that status must be a valid StoryStatus."""
        # Valid status should work
        story = UserStory(id="STORY-005", title="Test story", description="Test description", status=StoryStatus.DONE)
        assert story.status == StoryStatus.DONE

        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            UserStory(
                id="STORY-006",
                title="Test story",
                description="Test description",
                status="invalid_status",  # type: ignore
            )

    def test_user_story_priority_validation(self) -> None:
        """Test that priority must be a valid Priority."""
        # Valid priority should work
        story = UserStory(
            id="STORY-007", title="Test story", description="Test description", priority=Priority.CRITICAL
        )
        assert story.priority == Priority.CRITICAL

        # Invalid priority should raise ValidationError
        with pytest.raises(ValidationError):
            UserStory(
                id="STORY-008",
                title="Test story",
                description="Test description",
                priority="invalid_priority",  # type: ignore
            )

    def test_user_story_points_validation(self) -> None:
        """Test that points must be a positive integer if provided."""
        # Valid points should work
        story = UserStory(id="STORY-009", title="Test story", description="Test description", points=8)
        assert story.points == 8

        # None should work (optional field)
        story = UserStory(id="STORY-010", title="Test story", description="Test description", points=None)
        assert story.points is None

    def test_user_story_sprint_id_optional(self) -> None:
        """Test that sprint_id is optional."""
        # Without sprint_id
        story1 = UserStory(id="STORY-011", title="Test story", description="Test description")
        assert story1.sprint_id is None

        # With sprint_id
        story2 = UserStory(id="STORY-012", title="Test story", description="Test description", sprint_id="SPRINT-002")
        assert story2.sprint_id == "SPRINT-002"

    def test_user_story_serialization(self) -> None:
        """Test that UserStory can be serialized and deserialized."""
        original_story = UserStory(
            id="STORY-013",
            title="Test serialization",
            description="Test description",
            status=StoryStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            points=3,
            sprint_id="SPRINT-003",
            tags=["test"],
        )

        # Serialize to dict
        story_dict = original_story.model_dump()
        assert story_dict["id"] == "STORY-013"
        assert story_dict["title"] == "Test serialization"
        assert story_dict["status"] == "in_progress"
        assert story_dict["priority"] == "high"

        # Deserialize from dict
        restored_story = UserStory(**story_dict)
        assert restored_story.id == original_story.id
        assert restored_story.title == original_story.title
        assert restored_story.status == original_story.status
        assert restored_story.priority == original_story.priority
        assert restored_story.points == original_story.points
        assert restored_story.sprint_id == original_story.sprint_id

    def test_user_story_inherits_from_agile_artifact(self) -> None:
        """Test that UserStory inherits AgileArtifact properties."""
        story = UserStory(
            id="STORY-014",
            title="Test inheritance",
            description="Test description",
            created_by="test_user",
            tags=["inheritance", "test"],
        )

        # Should have AgileArtifact properties
        assert hasattr(story, "created_at")
        assert hasattr(story, "updated_at")
        assert hasattr(story, "created_by")
        assert hasattr(story, "tags")

        assert story.created_by == "test_user"
        assert story.tags == ["inheritance", "test"]
