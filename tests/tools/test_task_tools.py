"""Tests for task management tools."""

from unittest.mock import MagicMock

import pytest
from agile_mcp.models.task import TaskPriority
from agile_mcp.tools.base import ToolError
from agile_mcp.tools.task_tools import CreateTaskTool, DeleteTaskTool, GetTaskTool, ListTasksTool, UpdateTaskTool


class TestTaskTools:
    """Test cases for task management tools."""

    @pytest.fixture
    def mock_agent(self):
        """Fixture for a mocked agent."""
        agent = MagicMock()
        agent.project_manager.is_initialized.return_value = True
        return agent

    def test_create_task_success(self, mock_agent):
        """Test successful creation of a task."""
        create_tool = CreateTaskTool(mock_agent)
        mock_agent.task_service.create_task.return_value = MagicMock(id="TASK-1", title="Test Task")

        result = create_tool.apply(title="Test Task", description="A test task.")

        assert "Task 'Test Task' created successfully with ID TASK-1" in result.message
        mock_agent.task_service.create_task.assert_called_once_with(
            title="Test Task",
            description="A test task.",
            priority=TaskPriority.MEDIUM,
            story_id=None,
            assignee=None,
            estimated_hours=None,
            due_date=None,
            dependencies=[],
            tags=[],
        )

    def test_create_task_with_optional_params(self, mock_agent):
        """Test task creation with all optional parameters."""
        create_tool = CreateTaskTool(mock_agent)
        mock_agent.task_service.create_task.return_value = MagicMock(id="TASK-2", title="Another Task")

        result = create_tool.apply(
            title="Another Task",
            description="Another test task.",
            priority="high",
            story_id="STORY-1",
            tags="bug, frontend",
        )

        assert "Task 'Another Task' created successfully with ID TASK-2" in result.message
        mock_agent.task_service.create_task.assert_called_once_with(
            title="Another Task",
            description="Another test task.",
            priority=TaskPriority.HIGH,
            story_id="STORY-1",
            assignee=None,
            estimated_hours=None,
            due_date=None,
            dependencies=[],
            tags=["bug", "frontend"],
        )

    def test_create_task_invalid_priority(self, mock_agent):
        """Test task creation with an invalid priority."""
        create_tool = CreateTaskTool(mock_agent)

        with pytest.raises(ToolError, match="Invalid priority"):
            create_tool.apply(title="Test", description="Test", priority="invalid")

    def test_get_task_success(self, mock_agent):
        """Test successfully retrieving a task."""
        get_tool = GetTaskTool(mock_agent)
        mock_agent.task_service.get_task.return_value = MagicMock(id="TASK-1", title="Test Task")

        result = get_tool.apply(task_id="TASK-1")

        assert "Retrieved task: Test Task (ID: TASK-1)" in result.message
        mock_agent.task_service.get_task.assert_called_once_with("TASK-1")

    def test_get_task_not_found(self, mock_agent):
        """Test retrieving a task that does not exist."""
        get_tool = GetTaskTool(mock_agent)
        mock_agent.task_service.get_task.return_value = None

        with pytest.raises(ToolError, match="Task with ID NOT-FOUND not found"):
            get_tool.apply(task_id="NOT-FOUND")

    def test_update_task_success(self, mock_agent):
        """Test successfully updating a task."""
        update_tool = UpdateTaskTool(mock_agent)
        mock_agent.task_service.update_task.return_value = MagicMock(id="TASK-1", title="Updated Task")

        result = update_tool.apply(task_id="TASK-1", title="Updated Task")

        assert "Task 'Updated Task' updated successfully" in result.message
        mock_agent.task_service.update_task.assert_called_once_with("TASK-1", title="Updated Task")

    def test_update_task_not_found(self, mock_agent):
        """Test updating a task that does not exist."""
        update_tool = UpdateTaskTool(mock_agent)
        mock_agent.task_service.update_task.return_value = None

        with pytest.raises(ToolError, match="Task with ID NOT-FOUND not found"):
            update_tool.apply(task_id="NOT-FOUND", title="Does not exist")

    def test_delete_task_success(self, mock_agent):
        """Test successfully deleting a task."""
        delete_tool = DeleteTaskTool(mock_agent)
        mock_agent.task_service.get_task.return_value = MagicMock(id="TASK-1", title="Test Task")
        mock_agent.task_service.delete_task.return_value = True

        result = delete_tool.apply(task_id="TASK-1")

        assert "Task 'Test Task' (ID: TASK-1) deleted successfully" in result.message
        mock_agent.task_service.delete_task.assert_called_once_with("TASK-1")

    def test_delete_task_not_found(self, mock_agent):
        """Test deleting a task that does not exist."""
        delete_tool = DeleteTaskTool(mock_agent)
        mock_agent.task_service.get_task.return_value = None

        with pytest.raises(ToolError, match="Task with ID NOT-FOUND not found"):
            delete_tool.apply(task_id="NOT-FOUND")

    def test_list_tasks_success(self, mock_agent):
        """Test successfully listing tasks."""
        list_tool = ListTasksTool(mock_agent)
        mock_agent.task_service.list_tasks.return_value = [
            MagicMock(
                id="TASK-1",
                title="Task 1",
                status=MagicMock(value="todo"),
                priority=MagicMock(value="high"),
                assignee=None,
                story_id=None,
            ),
            MagicMock(
                id="TASK-2",
                title="Task 2",
                status=MagicMock(value="in_progress"),
                priority=MagicMock(value="medium"),
                assignee=None,
                story_id=None,
            ),
        ]

        result = list_tool.apply()

        assert "Found 2 tasks" in result.message
        assert "- TASK-1: Task 1 (todo)" in result.message
        assert "- TASK-2: Task 2 (in_progress)" in result.message
