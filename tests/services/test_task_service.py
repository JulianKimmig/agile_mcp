"""Tests for TaskService."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from agile_mcp.models.task import Task, TaskStatus
from agile_mcp.services.task_service import TaskService
from agile_mcp.storage.filesystem import AgileProjectManager


class TestTaskService:
    """Test TaskService functionality."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def project_manager(self, temp_project_dir):
        """Create an AgileProjectManager instance for testing."""
        manager = AgileProjectManager(temp_project_dir)
        manager.initialize()
        return manager

    @pytest.fixture
    def task_service(self, project_manager):
        """Create a TaskService instance for testing."""
        return TaskService(project_manager)

    def test_create_task_minimal(self, task_service):
        """Test creating a task with minimal information."""
        task = task_service.create_task(title="Fix login bug", description="The login form is not validating properly")

        assert task.title == "Fix login bug"
        assert task.description == "The login form is not validating properly"
        assert task.status == TaskStatus.TODO
        assert task.assignee is None
        assert task.story_id is None
        assert task.estimated_hours is None
        assert task.tags == []
        assert isinstance(task.id, str)
        assert task.id.startswith("TASK-")

    def test_create_task_complete(self, task_service):
        """Test creating a task with all fields."""
        task = task_service.create_task(
            title="Implement user registration",
            description="Create registration form with validation",
            status=TaskStatus.IN_PROGRESS,
            assignee="john.doe",
            story_id="STORY-001",
            estimated_hours=4.5,
            tags=["frontend", "authentication"],
        )

        assert task.title == "Implement user registration"
        assert task.description == "Create registration form with validation"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.assignee == "john.doe"
        assert task.story_id == "STORY-001"
        assert task.estimated_hours == 4.5
        assert task.tags == ["frontend", "authentication"]

    def test_create_task_invalid_hours(self, task_service):
        """Test that creating a task with negative hours raises ValueError."""
        with pytest.raises(ValueError, match="Estimated hours must be non-negative"):
            task_service.create_task(title="Test task", description="Test description", estimated_hours=-1.0)

    def test_get_task_exists(self, task_service):
        """Test retrieving an existing task."""
        # Create a task
        created_task = task_service.create_task(title="Test Task", description="Test Description")

        # Retrieve it
        retrieved_task = task_service.get_task(created_task.id)

        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.title == created_task.title
        assert retrieved_task.description == created_task.description

    def test_get_task_not_exists(self, task_service):
        """Test retrieving a non-existent task."""
        result = task_service.get_task("TASK-XXXX")
        assert result is None

    def test_update_task_single_field(self, task_service):
        """Test updating a single field of a task."""
        # Create a task
        task = task_service.create_task(title="Original Title", description="Original Description")

        # Update only the title
        updated_task = task_service.update_task(task.id, title="Updated Title")

        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.description == "Original Description"  # Unchanged
        assert updated_task.id == task.id

    def test_update_task_multiple_fields(self, task_service):
        """Test updating multiple fields of a task."""
        # Create a task
        task = task_service.create_task(title="Original Title", description="Original Description")

        # Update multiple fields
        updated_task = task_service.update_task(
            task.id, title="Updated Title", status=TaskStatus.IN_PROGRESS, assignee="jane.doe", estimated_hours=2.5
        )

        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.assignee == "jane.doe"
        assert updated_task.estimated_hours == 2.5
        assert updated_task.description == "Original Description"  # Unchanged

    def test_update_task_not_exists(self, task_service):
        """Test updating a non-existent task."""
        result = task_service.update_task("TASK-XXXX", title="New Title")
        assert result is None

    def test_update_task_invalid_hours(self, task_service):
        """Test that updating with negative hours raises ValueError."""
        # Create a task
        task = task_service.create_task(title="Test Task", description="Test Description")

        # Try to update with negative hours
        with pytest.raises(ValueError, match="Estimated hours must be non-negative"):
            task_service.update_task(task.id, estimated_hours=-1.0)

    def test_delete_task_exists(self, task_service):
        """Test deleting an existing task."""
        # Create a task
        task = task_service.create_task(title="Test Task", description="Test Description")

        # Delete it
        result = task_service.delete_task(task.id)
        assert result is True

        # Verify it's gone
        retrieved_task = task_service.get_task(task.id)
        assert retrieved_task is None

    def test_delete_task_not_exists(self, task_service):
        """Test deleting a non-existent task."""
        result = task_service.delete_task("TASK-XXXX")
        assert result is False

    def test_list_tasks_no_filter(self, task_service):
        """Test listing all tasks without filters."""
        # Create multiple tasks
        task1 = task_service.create_task("Task 1", "Description 1")
        task2 = task_service.create_task("Task 2", "Description 2")
        task3 = task_service.create_task("Task 3", "Description 3")

        # List all tasks
        tasks = task_service.list_tasks()

        assert len(tasks) == 3
        task_ids = [task.id for task in tasks]
        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id in task_ids

    def test_list_tasks_filter_by_status(self, task_service):
        """Test listing tasks filtered by status."""
        # Create tasks with different statuses
        task1 = task_service.create_task("Task 1", "Description 1", status=TaskStatus.TODO)
        task2 = task_service.create_task("Task 2", "Description 2", status=TaskStatus.IN_PROGRESS)
        task3 = task_service.create_task("Task 3", "Description 3", status=TaskStatus.TODO)

        # Filter by TODO status
        todo_tasks = task_service.list_tasks(status=TaskStatus.TODO)

        assert len(todo_tasks) == 2
        todo_ids = [task.id for task in todo_tasks]
        assert task1.id in todo_ids
        assert task3.id in todo_ids
        assert task2.id not in todo_ids

    def test_list_tasks_filter_by_assignee(self, task_service):
        """Test listing tasks filtered by assignee."""
        # Create tasks with different assignees
        task1 = task_service.create_task("Task 1", "Description 1", assignee="john.doe")
        task2 = task_service.create_task("Task 2", "Description 2", assignee="jane.smith")
        task3 = task_service.create_task("Task 3", "Description 3", assignee="john.doe")
        task4 = task_service.create_task("Task 4", "Description 4")  # No assignee

        # Filter by assignee
        john_tasks = task_service.list_tasks(assignee="john.doe")

        assert len(john_tasks) == 2
        john_ids = [task.id for task in john_tasks]
        assert task1.id in john_ids
        assert task3.id in john_ids
        assert task2.id not in john_ids
        assert task4.id not in john_ids

    def test_list_tasks_filter_by_story(self, task_service):
        """Test listing tasks filtered by story ID."""
        # Create tasks with different story IDs
        task1 = task_service.create_task("Task 1", "Description 1", story_id="STORY-001")
        task2 = task_service.create_task("Task 2", "Description 2", story_id="STORY-002")
        task3 = task_service.create_task("Task 3", "Description 3", story_id="STORY-001")
        task4 = task_service.create_task("Task 4", "Description 4")  # No story

        # Filter by story ID
        story_tasks = task_service.list_tasks(story_id="STORY-001")

        assert len(story_tasks) == 2
        story_ids = [task.id for task in story_tasks]
        assert task1.id in story_ids
        assert task3.id in story_ids
        assert task2.id not in story_ids
        assert task4.id not in story_ids

    def test_get_tasks_by_story(self, task_service):
        """Test getting tasks by story ID."""
        # Create tasks
        task1 = task_service.create_task("Task 1", "Description 1", story_id="STORY-001")
        task2 = task_service.create_task("Task 2", "Description 2", story_id="STORY-002")
        task3 = task_service.create_task("Task 3", "Description 3", story_id="STORY-001")

        # Get tasks for a specific story
        story_tasks = task_service.get_tasks_by_story("STORY-001")

        assert len(story_tasks) == 2
        task_ids = [task.id for task in story_tasks]
        assert task1.id in task_ids
        assert task3.id in task_ids
        assert task2.id not in task_ids

    def test_get_tasks_by_assignee(self, task_service):
        """Test getting tasks by assignee."""
        # Create tasks
        task1 = task_service.create_task("Task 1", "Description 1", assignee="john.doe")
        task2 = task_service.create_task("Task 2", "Description 2", assignee="jane.smith")
        task3 = task_service.create_task("Task 3", "Description 3", assignee="john.doe")

        # Get tasks for a specific assignee
        john_tasks = task_service.get_tasks_by_assignee("john.doe")

        assert len(john_tasks) == 2
        task_ids = [task.id for task in john_tasks]
        assert task1.id in task_ids
        assert task3.id in task_ids
        assert task2.id not in task_ids

    def test_get_unassigned_tasks(self, task_service):
        """Test getting unassigned tasks."""
        # Create tasks
        task1 = task_service.create_task("Task 1", "Description 1", assignee="john.doe")
        task2 = task_service.create_task("Task 2", "Description 2")  # Unassigned
        task3 = task_service.create_task("Task 3", "Description 3")  # Unassigned

        # Get unassigned tasks
        unassigned_tasks = task_service.get_unassigned_tasks()

        assert len(unassigned_tasks) == 2
        task_ids = [task.id for task in unassigned_tasks]
        assert task2.id in task_ids
        assert task3.id in task_ids
        assert task1.id not in task_ids

    def test_get_tasks_by_status(self, task_service):
        """Test getting tasks by status."""
        # Create tasks
        task1 = task_service.create_task("Task 1", "Description 1", status=TaskStatus.TODO)
        task2 = task_service.create_task("Task 2", "Description 2", status=TaskStatus.IN_PROGRESS)
        task3 = task_service.create_task("Task 3", "Description 3", status=TaskStatus.TODO)

        # Get tasks by status
        todo_tasks = task_service.get_tasks_by_status(TaskStatus.TODO)

        assert len(todo_tasks) == 2
        task_ids = [task.id for task in todo_tasks]
        assert task1.id in task_ids
        assert task3.id in task_ids
        assert task2.id not in task_ids

    def test_assign_task(self, task_service):
        """Test assigning a task to someone."""
        # Create a task
        task = task_service.create_task(title="Test Task", description="Test Description")
        assert task.assignee is None

        # Assign it
        updated_task = task_service.assign_task(task.id, "john.doe")

        assert updated_task is not None
        assert updated_task.assignee == "john.doe"

        # Verify persistence
        retrieved_task = task_service.get_task(task.id)
        assert retrieved_task.assignee == "john.doe"

    def test_change_task_status(self, task_service):
        """Test changing task status."""
        # Create a task
        task = task_service.create_task(title="Test Task", description="Test Description")
        assert task.status == TaskStatus.TODO

        # Change status
        updated_task = task_service.change_task_status(task.id, TaskStatus.IN_PROGRESS)

        assert updated_task is not None
        assert updated_task.status == TaskStatus.IN_PROGRESS

        # Verify persistence
        retrieved_task = task_service.get_task(task.id)
        assert retrieved_task.status == TaskStatus.IN_PROGRESS

    def test_task_persistence(self, task_service):
        """Test that tasks are properly persisted to filesystem."""
        # Create a task
        task = task_service.create_task(
            title="Persistence Test",
            description="Test task persistence",
            status=TaskStatus.IN_PROGRESS,
            assignee="test.user",
            story_id="STORY-TEST",
            estimated_hours=3.0,
            tags=["test", "persistence"],
        )

        # Verify the file exists in the correct status subfolder
        task_file = task_service.tasks_dir / task.status.value / f"{task.id}.yml"
        assert task_file.exists()

        # Create a new service instance (simulating restart)
        new_service = TaskService(task_service.project_manager)

        # Retrieve the task with the new service
        retrieved_task = new_service.get_task(task.id)

        assert retrieved_task is not None
        assert retrieved_task.title == "Persistence Test"
        assert retrieved_task.description == "Test task persistence"
        assert retrieved_task.status == TaskStatus.IN_PROGRESS
        assert retrieved_task.assignee == "test.user"
        assert retrieved_task.story_id == "STORY-TEST"
        assert retrieved_task.estimated_hours == 3.0
        assert retrieved_task.tags == ["test", "persistence"]
