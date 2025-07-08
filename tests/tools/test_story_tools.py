"""Tests for story management tools."""

import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import Mock

import json
from agile_mcp.tools.story_tools import CreateStoryTool, GetStoryTool, UpdateStoryTool, ListStoriesTool, DeleteStoryTool
from agile_mcp.tools.base import ToolResult, ToolError
from agile_mcp.models.story import StoryStatus, Priority
from agile_mcp.storage.filesystem import AgileProjectManager
from agile_mcp.services.story_service import StoryService


class MockToolResult:
    """Mock object to provide ToolResult-like interface for parsed JSON responses."""

    def __init__(self, json_response: str):
        """Parse JSON response and create mock result object."""
        parsed = json.loads(json_response)
        self.success = parsed.get("success", False)
        self.message = parsed.get("message", "")
        self.data = parsed.get("data", None)


def parse_tool_result(json_response: str) -> MockToolResult:
    """Parse JSON response from apply_ex into a ToolResult-like object."""
    return MockToolResult(json_response)


class TestCreateStoryTool:
    """Test cases for CreateStoryTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

        # Initialize project and services
        self.project_manager = AgileProjectManager(str(self.project_path))
        self.project_manager.initialize()

        # Create mock agent with story service
        self.mock_agent = Mock()
        self.mock_agent.story_service = StoryService(self.project_manager)

        # Create tool instance
        self.tool = CreateStoryTool(self.mock_agent)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_create_story_tool_name(self) -> None:
        """Test that the tool name is correct."""
        assert self.tool.get_name() == "create_story"

    def test_create_story_tool_description(self) -> None:
        """Test that the tool has a description."""
        description = self.tool.get_description()
        assert "create" in description.lower()
        assert "story" in description.lower()

    def test_create_story_with_minimal_params(self) -> None:
        """Test creating a story with only required parameters."""
        result = parse_tool_result(
            self.tool.apply_ex(title="As a user, I want to login", description="User authentication functionality")
        )
        assert isinstance(result, MockToolResult)
        assert result.success is True
        assert "created successfully" in result.message.lower()
        assert result.data is not None
        assert "id" in result.data
        assert result.data["title"] == "As a user, I want to login"

    def test_create_story_with_all_params(self) -> None:
        """Test creating a story with all parameters."""
        result = parse_tool_result(
            self.tool.apply_ex(
                title="As a user, I want to logout",
                description="User logout functionality",
                priority="high",
                points=5,
                tags="auth,security",
            )
        )
        assert isinstance(result, MockToolResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["priority"] == "high"
        assert result.data["points"] == 5
        assert result.data["tags"] == ["auth", "security"]

    def test_create_story_validates_required_fields(self) -> None:
        """Test that required fields are validated."""
        # Missing title
        result = parse_tool_result(self.tool.apply_ex(description="Test description"))
        assert result.success is False
        assert "title" in result.message.lower()

        # Missing description
        result = parse_tool_result(self.tool.apply_ex(title="Test title"))
        assert result.success is False
        assert "description" in result.message.lower()

    def test_create_story_validates_story_points(self) -> None:
        """Test that story points are validated to be Fibonacci numbers."""
        result = parse_tool_result(
            self.tool.apply_ex(
                title="Test story",
                description="Test description",
                points=4,  # Invalid Fibonacci number
            )
        )
        assert result.success is False
        assert "fibonacci" in result.message.lower()

    def test_create_story_validates_priority(self) -> None:
        """Test that priority values are validated."""
        result = parse_tool_result(
            self.tool.apply_ex(title="Test story", description="Test description", priority="invalid")
        )
        assert result.success is False
        assert "priority" in result.message.lower()

    def test_create_story_parses_tags(self) -> None:
        """Test that tags string is properly parsed."""
        result = parse_tool_result(
            self.tool.apply_ex(title="Test story", description="Test description", tags="tag1, tag2,tag3 , tag4")
        )
        assert result.success is True
        assert result.data["tags"] == ["tag1", "tag2", "tag3", "tag4"]


class TestGetStoryTool:
    """Test cases for GetStoryTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

        # Initialize project and services
        self.project_manager = AgileProjectManager(str(self.project_path))
        self.project_manager.initialize()

        # Create mock agent with story service
        self.mock_agent = Mock()
        self.mock_agent.story_service = StoryService(self.project_manager)

        # Create test story
        self.test_story = self.mock_agent.story_service.create_story(
            title="Test Story", description="Test Description", priority=Priority.HIGH
        )

        # Create tool instance
        self.tool = GetStoryTool(self.mock_agent)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_get_story_tool_name(self) -> None:
        """Test that the tool name is correct."""
        assert self.tool.get_name() == "get_story"

    def test_get_existing_story(self) -> None:
        """Test retrieving an existing story."""
        result = parse_tool_result(self.tool.apply_ex(story_id=self.test_story.id))
        assert isinstance(result, MockToolResult)
        assert result.success is True
        assert result.data is not None
        assert result.data["id"] == self.test_story.id
        assert result.data["title"] == "Test Story"
        assert result.data["priority"] == "high"

    def test_get_nonexistent_story(self) -> None:
        """Test retrieving a non-existent story."""
        result = parse_tool_result(self.tool.apply_ex(story_id="STORY-NONEXISTENT"))
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_get_story_validates_id_required(self) -> None:
        """Test that story_id is required."""
        result = parse_tool_result(self.tool.apply_ex())

        assert result.success is False
        assert "story_id" in result.message.lower()


class TestUpdateStoryTool:
    """Test cases for UpdateStoryTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

        # Initialize project and services
        self.project_manager = AgileProjectManager(str(self.project_path))
        self.project_manager.initialize()

        # Create mock agent with story service
        self.mock_agent = Mock()
        self.mock_agent.story_service = StoryService(self.project_manager)

        # Create test story
        self.test_story = self.mock_agent.story_service.create_story(
            title="Original Title", description="Original Description"
        )

        # Create tool instance
        self.tool = UpdateStoryTool(self.mock_agent)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_update_story_tool_name(self) -> None:
        """Test that the tool name is correct."""
        assert self.tool.get_name() == "update_story"

    def test_update_story_title(self) -> None:
        """Test updating a story title."""
        result = parse_tool_result(self.tool.apply_ex(story_id=self.test_story.id, title="Updated Title"))
        assert result.success is True
        assert result.data["title"] == "Updated Title"
        assert result.data["description"] == "Original Description"  # Unchanged

    def test_update_story_multiple_fields(self) -> None:
        """Test updating multiple story fields."""
        result = parse_tool_result(
            self.tool.apply_ex(
                story_id=self.test_story.id,
                title="New Title",
                description="New Description",
                priority="high",
                status="in_progress",
                points=8,
            )
        )
        assert result.success is True
        assert result.data["title"] == "New Title"
        assert result.data["description"] == "New Description"
        assert result.data["priority"] == "high"
        assert result.data["status"] == "in_progress"
        assert result.data["points"] == 8

    def test_update_nonexistent_story(self) -> None:
        """Test updating a non-existent story."""
        result = parse_tool_result(self.tool.apply_ex(story_id="STORY-NONEXISTENT", title="Updated Title"))
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_update_story_validates_story_id_required(self) -> None:
        """Test that story_id is required."""
        result = parse_tool_result(self.tool.apply_ex(title="Updated Title"))
        assert result.success is False
        assert "story_id" in result.message.lower()


class TestListStoriesTool:
    """Test cases for ListStoriesTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

        # Initialize project and services
        self.project_manager = AgileProjectManager(str(self.project_path))
        self.project_manager.initialize()

        # Create mock agent with story service
        self.mock_agent = Mock()
        self.mock_agent.story_service = StoryService(self.project_manager)

        # Create test stories
        self.story1 = self.mock_agent.story_service.create_story(
            title="Story 1", description="Description 1", priority=Priority.HIGH
        )
        self.story2 = self.mock_agent.story_service.create_story(
            title="Story 2", description="Description 2", priority=Priority.LOW
        )
        self.mock_agent.story_service.update_story(self.story2.id, status=StoryStatus.IN_PROGRESS)

        # Create tool instance
        self.tool = ListStoriesTool(self.mock_agent)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_list_stories_tool_name(self) -> None:
        """Test that the tool name is correct."""
        assert self.tool.get_name() == "list_stories"

    def test_list_all_stories(self) -> None:
        """Test listing all stories."""
        result = parse_tool_result(self.tool.apply_ex())

        assert result.success is True
        assert result.data is not None
        assert "stories" in result.data
        assert len(result.data["stories"]) == 2

    def test_list_stories_by_status(self) -> None:
        """Test filtering stories by status."""
        result = parse_tool_result(self.tool.apply_ex(status="in_progress"))
        assert result.success is True
        assert len(result.data["stories"]) == 1
        assert result.data["stories"][0]["id"] == self.story2.id

    def test_list_stories_by_priority(self) -> None:
        """Test filtering stories by priority."""
        result = parse_tool_result(self.tool.apply_ex(priority="high"))
        assert result.success is True
        assert len(result.data["stories"]) == 1
        assert result.data["stories"][0]["id"] == self.story1.id

    def test_list_stories_validates_filters(self) -> None:
        """Test that invalid filter values are rejected."""
        result = parse_tool_result(self.tool.apply_ex(status="invalid_status"))
        assert result.success is False
        assert "status" in result.message.lower()

    def test_apply_returns_structured_data(self) -> None:
        """Test that apply() returns structured data directly (new architecture)."""
        # This demonstrates the improved separation of concerns:
        # apply() returns structured data, apply_ex() handles formatting

        # Test with no filters
        data = self.tool.apply()

        assert isinstance(data, dict)
        assert "stories" in data
        assert "count" in data
        assert "filters" in data
        assert data["count"] == 2
        assert len(data["stories"]) == 2

        # Verify structured story data
        story_data = data["stories"][0]
        assert "id" in story_data
        assert "title" in story_data
        assert "description" in story_data
        assert "status" in story_data
        assert "priority" in story_data

        # Test with filters
        filtered_data = self.tool.apply(status="in_progress")
        assert filtered_data["count"] == 1
        assert filtered_data["filters"]["status"] == "in_progress"
        assert len(filtered_data["stories"]) == 1

    def test_message_formatting_from_structured_data(self) -> None:
        """Test that _format_message_from_data correctly formats messages from structured data."""
        # Get structured data from apply()
        data = self.tool.apply()

        # Test message formatting
        message = self.tool._format_message_from_data(data)

        assert isinstance(message, str)
        assert "Found 2 stories" in message
        assert "Story 1" in message
        assert "Story 2" in message

        # Test with filtered data
        filtered_data = self.tool.apply(status="in_progress", priority="low")
        filtered_message = self.tool._format_message_from_data(filtered_data)

        assert "Found 1 stories" in filtered_message
        assert "status 'in_progress'" in filtered_message
        assert "priority 'low'" in filtered_message

        # Test empty results
        empty_data = {"stories": [], "count": 0, "filters": {}}
        empty_message = self.tool._format_message_from_data(empty_data)
        assert "No stories found" in empty_message


class TestDeleteStoryTool:
    """Test cases for DeleteStoryTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir) / "test_project"
        self.project_path.mkdir()

        # Initialize project and services
        self.project_manager = AgileProjectManager(str(self.project_path))
        self.project_manager.initialize()

        # Create mock agent with story service
        self.mock_agent = Mock()
        self.mock_agent.story_service = StoryService(self.project_manager)

        # Create test story
        self.test_story = self.mock_agent.story_service.create_story(
            title="Story to Delete", description="This story will be deleted"
        )

        # Create tool instance
        self.tool = DeleteStoryTool(self.mock_agent)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_delete_story_tool_name(self) -> None:
        """Test that the tool name is correct."""
        assert self.tool.get_name() == "delete_story"

    def test_delete_existing_story(self) -> None:
        """Test deleting an existing story."""
        result = parse_tool_result(self.tool.apply_ex(story_id=self.test_story.id))
        assert result.success is True
        assert "deleted successfully" in result.message.lower()

        # Verify story is actually deleted
        deleted_story = self.mock_agent.story_service.get_story(self.test_story.id)
        assert deleted_story is None

    def test_delete_nonexistent_story(self) -> None:
        """Test deleting a non-existent story."""
        result = parse_tool_result(self.tool.apply_ex(story_id="STORY-NONEXISTENT"))
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_delete_story_validates_id_required(self) -> None:
        """Test that story_id is required."""
        result = parse_tool_result(self.tool.apply_ex())

        assert result.success is False
        assert "story_id" in result.message.lower()
