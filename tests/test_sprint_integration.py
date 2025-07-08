"""Integration tests for Sprint functionality in the Agile MCP Server."""

import tempfile
from pathlib import Path
import pytest
import json

from src.agile_mcp.server import AgileMCPServer


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


class TestSprintIntegration:
    """Test Sprint functionality integration with MCP server."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def server(self, temp_project_dir):
        """Create and initialize an MCP server for testing."""
        server = AgileMCPServer(str(temp_project_dir))
        server._initialize_services()
        return server

    def test_create_sprint_tool(self, server):
        """Test creating a sprint using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool

        tool = CreateSprintTool(server)

        # Test creating a basic sprint
        result = tool.apply_ex(
            name="Sprint 1", goal="Implement authentication features", tags="authentication,security"
        )

        assert "Sprint 'Sprint 1' created successfully" in result
        assert "SPRINT-" in result

    def test_get_sprint_tool(self, server):
        """Test retrieving a sprint using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool, GetSprintTool

        # First create a sprint
        create_tool = CreateSprintTool(server)
        create_result = parse_tool_result(create_tool.apply_ex(name="Test Sprint", goal="Test sprint for retrieval"))

        assert create_result.success
        sprint_id = create_result.data["id"]

        # Now retrieve it
        get_tool = GetSprintTool(server)
        result = get_tool.apply_ex(sprint_id=sprint_id)

        assert "Retrieved sprint: Test Sprint" in result
        assert sprint_id in result
        assert "Status: planning" in result

    def test_list_sprints_tool(self, server):
        """Test listing sprints using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool, ListSprintsTool

        # Create a few sprints
        create_tool = CreateSprintTool(server)
        create_tool.apply_ex(name="Sprint 1", goal="First sprint")
        create_tool.apply_ex(name="Sprint 2", goal="Second sprint")

        # List all sprints
        list_tool = ListSprintsTool(server)
        result = list_tool.apply_ex()

        assert "Found 2 sprints" in result

    def test_update_sprint_tool(self, server):
        """Test updating a sprint using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool, UpdateSprintTool

        # Create a sprint
        create_tool = CreateSprintTool(server)
        create_result = parse_tool_result(create_tool.apply_ex(name="Original Sprint", goal="Original goal"))

        assert create_result.success
        sprint_id = create_result.data["id"]

        # Update the sprint
        update_tool = UpdateSprintTool(server)
        result = update_tool.apply_ex(sprint_id=sprint_id, name="Updated Sprint", goal="Updated goal", status="active")

        assert "Sprint 'Updated Sprint' updated successfully" in result

    def test_manage_sprint_stories_tool(self, server):
        """Test adding/removing stories from sprint using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool, ManageSprintStoriesTool
        from src.agile_mcp.tools.story_tools import CreateStoryTool

        # Create a sprint and a story
        sprint_tool = CreateSprintTool(server)
        sprint_result = parse_tool_result(sprint_tool.apply_ex(name="Test Sprint"))
        assert sprint_result.success
        sprint_id = sprint_result.data["id"]

        story_tool = CreateStoryTool(server)
        story_result = parse_tool_result(story_tool.apply_ex(title="Test Story", description="A test story"))
        assert story_result.success
        story_id = story_result.data["id"]

        # Add story to sprint
        manage_tool = ManageSprintStoriesTool(server)
        add_result = manage_tool.apply_ex(sprint_id=sprint_id, action="add", story_id=story_id)

        assert f"Story '{story_id}' added to sprint '{sprint_id}'" in add_result

        # Remove story from sprint
        remove_result = manage_tool.apply_ex(sprint_id=sprint_id, action="remove", story_id=story_id)

        assert f"Story '{story_id}' removed from sprint '{sprint_id}'" in remove_result

    def test_get_sprint_progress_tool(self, server):
        """Test getting sprint progress using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool, GetSprintProgressTool

        # Create a sprint
        create_tool = CreateSprintTool(server)
        create_result = parse_tool_result(
            create_tool.apply_ex(name="Progress Test Sprint", goal="Test progress tracking")
        )

        assert create_result.success
        sprint_id = create_result.data["id"]

        # Get progress
        progress_tool = GetSprintProgressTool(server)
        result = progress_tool.apply_ex(sprint_id=sprint_id)

        assert "Sprint 'Progress Test Sprint' progress" in result
        assert "planning" in result

    def test_get_active_sprint_tool(self, server):
        """Test getting the active sprint using the tool interface."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool, UpdateSprintTool, GetActiveSprintTool

        # Initially no active sprint
        active_tool = GetActiveSprintTool(server)
        result = parse_tool_result(active_tool.apply_ex())
        assert "No active sprint found" in result.message

        # Create and activate a sprint
        create_tool = CreateSprintTool(server)
        create_result = parse_tool_result(create_tool.apply_ex(name="Active Sprint"))
        assert create_result.success
        sprint_id = create_result.data["id"]

        update_tool = UpdateSprintTool(server)
        update_tool.apply_ex(sprint_id=sprint_id, status="active")

        # Now there should be an active sprint
        result = active_tool.apply_ex()
        assert "Active sprint: Active Sprint" in result
        assert sprint_id in result

    def test_sprint_workflow_integration(self, server):
        """Test a complete sprint workflow integration."""
        from src.agile_mcp.tools.sprint_tools import (
            CreateSprintTool,
            UpdateSprintTool,
            ManageSprintStoriesTool,
            GetSprintProgressTool,
            GetActiveSprintTool,
        )
        from src.agile_mcp.tools.story_tools import CreateStoryTool

        # 1. Create a sprint
        sprint_tool = CreateSprintTool(server)
        sprint_result = parse_tool_result(
            sprint_tool.apply_ex(
                name="Integration Test Sprint",
                goal="Test complete workflow",
                start_date="2024-01-15",
                end_date="2024-01-29",
            )
        )
        assert sprint_result.success
        sprint_id = sprint_result.data["id"]

        # 2. Create some stories
        story_tool = CreateStoryTool(server)
        story1_result = parse_tool_result(
            story_tool.apply_ex(title="User Authentication", description="Implement user login and registration")
        )
        story2_result = parse_tool_result(
            story_tool.apply_ex(title="Dashboard UI", description="Create user dashboard interface")
        )
        assert story1_result.success and story2_result.success
        story1_id = story1_result.data["id"]
        story2_id = story2_result.data["id"]

        # 3. Add stories to sprint
        manage_tool = ManageSprintStoriesTool(server)
        manage_tool.apply_ex(sprint_id=sprint_id, action="add", story_id=story1_id)
        manage_tool.apply_ex(sprint_id=sprint_id, action="add", story_id=story2_id)

        # 4. Start the sprint
        update_tool = UpdateSprintTool(server)
        update_tool.apply_ex(sprint_id=sprint_id, status="active")

        # 5. Verify it's the active sprint
        active_tool = GetActiveSprintTool(server)
        active_result = parse_tool_result(active_tool.apply_ex())
        assert active_result.success
        assert active_result.data["active_sprint"]["id"] == sprint_id
        assert len(active_result.data["active_sprint"]["story_ids"]) == 2

        # 6. Check progress
        progress_tool = GetSprintProgressTool(server)
        progress_result = parse_tool_result(progress_tool.apply_ex(sprint_id=sprint_id))
        assert progress_result.success
        assert progress_result.data["progress"]["status"] == "active"
        assert progress_result.data["progress"]["story_count"] == 2

        # 7. Complete the sprint
        update_tool.apply_ex(sprint_id=sprint_id, status="completed")

        # 8. Verify no active sprint now
        active_result = active_tool.apply_ex()
        assert "No active sprint found" in active_result

    def test_sprint_date_validation(self, server):
        """Test that sprint date validation works correctly."""
        from src.agile_mcp.tools.sprint_tools import CreateSprintTool

        tool = CreateSprintTool(server)

        # Test invalid date format
        result = tool.apply_ex(name="Bad Date Sprint", start_date="invalid-date")
        assert "Tool Error:" in result
        assert "Invalid start_date format" in result

        # Test end date before start date
        result = tool.apply_ex(name="Bad Range Sprint", start_date="2024-01-29", end_date="2024-01-15")
        assert "Tool Error:" in result
        assert "End date must be after start date" in result

    def test_sprint_error_handling(self, server):
        """Test error handling in sprint tools."""
        from src.agile_mcp.tools.sprint_tools import GetSprintTool, UpdateSprintTool

        # Test getting non-existent sprint
        get_tool = GetSprintTool(server)
        result = get_tool.apply_ex(sprint_id="SPRINT-NONEXISTENT")
        assert "Tool Error:" in result
        assert "not found" in result

        # Test updating non-existent sprint
        update_tool = UpdateSprintTool(server)
        result = update_tool.apply_ex(sprint_id="SPRINT-NONEXISTENT", name="New Name")
        assert "Tool Error:" in result
        assert "not found" in result
