"""Tests for overview tools."""

import tempfile

import pytest

from agile_mcp.models.story import StoryStatus, Priority
from agile_mcp.server import AgileMCPServer
from agile_mcp.tools.overview_tools import GetProjectOverviewTool


@pytest.fixture
def server_with_project():
    """Create a server with a temporary project."""
    with tempfile.TemporaryDirectory() as temp_dir:
        server = AgileMCPServer()
        server.set_project_path(temp_dir)
        yield server


def test_get_project_overview_empty_project(server_with_project):
    """Test getting overview of an empty project."""
    tool = GetProjectOverviewTool(server_with_project)
    result = tool.apply()

    assert result.success is True
    assert "Project Overview" in result.message
    assert result.data is not None

    data = result.data
    assert data["summary"]["total_epics"] == 0
    assert data["summary"]["total_sprints"] == 0
    assert data["summary"]["total_stories"] == 0
    assert data["summary"]["total_tasks"] == 0
    assert len(data["epics"]) == 0
    assert len(data["sprints"]) == 0
    assert len(data["stories"]) == 0
    assert len(data["tasks"]) == 0


def test_get_project_overview_with_data(server_with_project):
    """Test getting overview of a project with data."""
    # Create some test data
    epic = server_with_project.epic_service.create_epic(title="Test Epic", description="A test epic")

    sprint = server_with_project.sprint_service.create_sprint(name="Test Sprint", goal="Test sprint goal")

    story = server_with_project.story_service.create_story(
        title="Test Story", description="A test story", sprint_id=sprint.id
    )

    task = server_with_project.task_service.create_task(title="Test Task", description="A test task", story_id=story.id)

    # Update epic to include the actual story ID
    server_with_project.epic_service.add_story_to_epic(epic.id, story.id)

    # Update sprint to include the story ID
    server_with_project.sprint_service.add_story_to_sprint(sprint.id, story.id)

    # Test the overview tool
    tool = GetProjectOverviewTool(server_with_project)
    result = tool.apply()

    assert result.success is True
    assert "Project Overview" in result.message
    assert result.data is not None

    data = result.data
    assert data["summary"]["total_epics"] == 1
    assert data["summary"]["total_sprints"] == 1
    assert data["summary"]["total_stories"] == 1
    assert data["summary"]["total_tasks"] == 1

    # Check that all data is included
    assert len(data["epics"]) == 1
    assert len(data["sprints"]) == 1
    assert len(data["stories"]) == 1
    assert len(data["tasks"]) == 1

    # Check epic data
    epic_data = data["epics"][0]
    assert epic_data["id"] == epic.id
    assert epic_data["title"] == "Test Epic"
    assert story.id in epic_data["story_ids"]

    # Check sprint data
    sprint_data = data["sprints"][0]
    assert sprint_data["id"] == sprint.id
    assert sprint_data["name"] == "Test Sprint"
    assert story.id in sprint_data["story_ids"]

    # Check story data
    story_data = data["stories"][0]
    assert story_data["id"] == story.id
    assert story_data["title"] == "Test Story"
    assert story_data["epic_id"] == epic.id
    assert story_data["sprint_id"] == sprint.id

    # Check task data
    task_data = data["tasks"][0]
    assert task_data["id"] == task.id
    assert task_data["title"] == "Test Task"
    assert task_data["story_id"] == story.id

    # Check relationships
    relationships = data["relationships"]
    assert relationships["epic_stories"][epic.id] == [story.id]
    assert relationships["sprint_stories"][sprint.id] == [story.id]
    assert relationships["story_tasks"][story.id] == [task.id]


def test_get_project_overview_filtering(server_with_project):
    """Test filtering options for the overview tool."""
    # Create completed story
    server_with_project.story_service.create_story(
        title="Completed Story", description="A completed story", status=StoryStatus.DONE
    )

    # Create in-progress story
    story2 = server_with_project.story_service.create_story(
        title="In Progress Story", description="An in-progress story", status=StoryStatus.IN_PROGRESS
    )

    # Test with include_completed=True (default)
    tool = GetProjectOverviewTool(server_with_project)
    result = tool.apply(include_completed=True)
    assert result.data["summary"]["total_stories"] == 2

    # Test with include_completed=False
    result = tool.apply(include_completed=False)
    assert result.data["summary"]["total_stories"] == 1
    assert result.data["stories"][0]["id"] == story2.id


def test_get_project_overview_no_project():
    """Test overview tool without project set."""
    server = AgileMCPServer()
    tool = GetProjectOverviewTool(server)
    result = tool.apply_ex()  # Use apply_ex to get proper error handling

    assert result.success is False
    assert "No project directory is set" in result.message


def test_get_project_overview_status_breakdown(server_with_project):
    """Test status breakdown in overview."""
    # Create stories with different statuses
    server_with_project.story_service.create_story(title="Story 1", description="Desc 1", status=StoryStatus.TODO)
    server_with_project.story_service.create_story(
        title="Story 2", description="Desc 2", status=StoryStatus.IN_PROGRESS
    )
    server_with_project.story_service.create_story(title="Story 3", description="Desc 3", status=StoryStatus.DONE)

    tool = GetProjectOverviewTool(server_with_project)
    result = tool.apply()

    status_breakdown = result.data["summary"]["status_breakdown"]["stories"]
    assert status_breakdown["todo"] == 1
    assert status_breakdown["in_progress"] == 1
    assert status_breakdown["done"] == 1


def test_get_project_overview_priority_breakdown(server_with_project):
    """Test priority breakdown in overview."""
    # Create stories with different priorities
    server_with_project.story_service.create_story(title="Story 1", description="Desc 1", priority=Priority.HIGH)
    server_with_project.story_service.create_story(title="Story 2", description="Desc 2", priority=Priority.MEDIUM)
    server_with_project.story_service.create_story(title="Story 3", description="Desc 3", priority=Priority.LOW)

    tool = GetProjectOverviewTool(server_with_project)
    result = tool.apply()

    priority_breakdown = result.data["summary"]["priority_breakdown"]["stories"]
    assert priority_breakdown["high"] == 1
    assert priority_breakdown["medium"] == 1
    assert priority_breakdown["low"] == 1
