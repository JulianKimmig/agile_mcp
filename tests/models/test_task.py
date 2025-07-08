"""Tests for Task model."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from agile_mcp.models.task import Task, TaskStatus
from agile_mcp.models.base import AgileArtifact


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_task_status_values(self):
        """Test that TaskStatus has correct values."""
        assert TaskStatus.TODO == "todo"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.DONE == "done"
        assert TaskStatus.BLOCKED == "blocked"

    def test_task_status_from_string(self):
        """Test creating TaskStatus from string."""
        assert TaskStatus("todo") == TaskStatus.TODO
        assert TaskStatus("in_progress") == TaskStatus.IN_PROGRESS
        assert TaskStatus("done") == TaskStatus.DONE
        assert TaskStatus("blocked") == TaskStatus.BLOCKED


class TestTask:
    """Test Task model."""

    def test_task_inherits_from_agile_artifact(self):
        """Test that Task inherits from AgileArtifact."""
        assert issubclass(Task, AgileArtifact)

    def test_create_minimal_task(self):
        """Test creating a task with minimal required fields."""
        task = Task(id="TASK-001", title="Fix login bug", description="The login form is not validating email properly")

        assert task.id == "TASK-001"
        assert task.title == "Fix login bug"
        assert task.description == "The login form is not validating email properly"
        assert task.status == TaskStatus.TODO  # default
        assert task.assignee is None  # default
        assert task.story_id is None  # default
        assert task.estimated_hours is None  # default

        # Check inherited fields
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)
        assert task.created_by is None
        assert task.tags == []

    def test_create_complete_task(self):
        """Test creating a task with all fields."""
        task = Task(
            id="TASK-002",
            title="Implement user registration",
            description="Create registration form with email validation",
            status=TaskStatus.IN_PROGRESS,
            assignee="john.doe",
            story_id="story_123",
            estimated_hours=4.5,
            created_by="product.owner",
            tags=["frontend", "authentication"],
        )

        assert task.title == "Implement user registration"
        assert task.description == "Create registration form with email validation"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.assignee == "john.doe"
        assert task.story_id == "story_123"
        assert task.estimated_hours == 4.5
        assert task.created_by == "product.owner"
        assert task.tags == ["frontend", "authentication"]

    def test_id_is_required(self):
        """Test that ID is required."""
        with pytest.raises(ValidationError) as exc_info:
            Task(title="Some title", description="Some description")

        assert "id" in str(exc_info.value)

    def test_title_is_required(self):
        """Test that title is required."""
        with pytest.raises(ValidationError) as exc_info:
            Task(id="TASK-003", description="Some description")

        assert "title" in str(exc_info.value)

    def test_description_is_required(self):
        """Test that description is required."""
        with pytest.raises(ValidationError) as exc_info:
            Task(id="TASK-004", title="Some title")

        assert "description" in str(exc_info.value)

    def test_status_validation(self):
        """Test that status must be valid TaskStatus."""
        # Valid status
        task = Task(id="TASK-005", title="Test task", description="Test description", status=TaskStatus.BLOCKED)
        assert task.status == TaskStatus.BLOCKED

        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            Task(id="TASK-006", title="Test task", description="Test description", status="invalid_status")

    def test_assignee_optional(self):
        """Test that assignee is optional."""
        task = Task(id="TASK-007", title="Test task", description="Test description")
        assert task.assignee is None

        task_with_assignee = Task(
            id="TASK-008", title="Test task", description="Test description", assignee="jane.smith"
        )
        assert task_with_assignee.assignee == "jane.smith"

    def test_story_id_optional(self):
        """Test that story_id is optional."""
        task = Task(id="TASK-009", title="Test task", description="Test description")
        assert task.story_id is None

        task_with_story = Task(id="TASK-010", title="Test task", description="Test description", story_id="story_456")
        assert task_with_story.story_id == "story_456"

    def test_estimated_hours_validation(self):
        """Test estimated_hours validation."""
        # None is valid (default)
        task = Task(id="TASK-011", title="Test task", description="Test description")
        assert task.estimated_hours is None

        # Positive float is valid
        task_with_hours = Task(id="TASK-012", title="Test task", description="Test description", estimated_hours=8.5)
        assert task_with_hours.estimated_hours == 8.5

        # Zero is valid
        task_zero_hours = Task(id="TASK-013", title="Test task", description="Test description", estimated_hours=0.0)
        assert task_zero_hours.estimated_hours == 0.0

        # Negative hours should raise ValidationError
        with pytest.raises(ValidationError):
            Task(id="TASK-014", title="Test task", description="Test description", estimated_hours=-1.0)

    def test_task_serialization(self):
        """Test that task can be serialized to dict."""
        task = Task(
            id="TASK-015",
            title="Test serialization",
            description="Test task serialization",
            status=TaskStatus.IN_PROGRESS,
            assignee="test.user",
            story_id="story_789",
            estimated_hours=2.5,
            tags=["backend", "api"],
        )

        task_dict = task.model_dump()

        assert task_dict["id"] == "TASK-015"
        assert task_dict["title"] == "Test serialization"
        assert task_dict["description"] == "Test task serialization"
        assert task_dict["status"] == "in_progress"
        assert task_dict["assignee"] == "test.user"
        assert task_dict["story_id"] == "story_789"
        assert task_dict["estimated_hours"] == 2.5
        assert task_dict["tags"] == ["backend", "api"]
        assert "created_at" in task_dict
        assert "updated_at" in task_dict

    def test_task_deserialization(self):
        """Test that task can be created from dict."""
        task_data = {
            "id": "TASK-016",
            "title": "Test deserialization",
            "description": "Test task deserialization",
            "status": "blocked",
            "assignee": "dev.user",
            "story_id": "story_101",
            "estimated_hours": 1.5,
            "tags": ["testing"],
        }

        task = Task(**task_data)

        assert task.id == "TASK-016"
        assert task.title == "Test deserialization"
        assert task.description == "Test task deserialization"
        assert task.status == TaskStatus.BLOCKED
        assert task.assignee == "dev.user"
        assert task.story_id == "story_101"
        assert task.estimated_hours == 1.5
        assert task.tags == ["testing"]

    def test_task_update_timestamp(self):
        """Test that updated_at changes when task is modified."""
        task = Task(id="TASK-017", title="Original title", description="Original description")
        original_updated_at = task.updated_at

        # Simulate some time passing
        import time

        time.sleep(0.01)

        # Update the task
        updated_task = task.model_copy(update={"title": "Updated title"})
        updated_task.updated_at = datetime.now()

        assert updated_task.updated_at > original_updated_at
        assert updated_task.title == "Updated title"
        assert updated_task.description == "Original description"

    def test_task_equality(self):
        """Test task equality based on ID."""
        task1 = Task(id="TASK-018", title="Task 1", description="First task")

        task2 = Task(id="TASK-019", title="Task 2", description="Second task")

        # Different tasks should not be equal
        assert task1 != task2

        # Same task with different attributes should be equal (same ID)
        task1_copy = task1.model_copy(update={"title": "Modified Task 1"})
        assert task1_copy.id == task1.id  # Same ID due to copy

    def test_task_string_representation(self):
        """Test string representation of task."""
        task = Task(id="TASK-020", title="Sample Task", description="A sample task for testing")

        # Should include key identifying information
        str_repr = str(task)
        assert "Sample Task" in str_repr
        assert task.id in str_repr
