"""Tests for burndown chart tool."""

from unittest.mock import MagicMock, patch

import pytest
from agile_mcp.tools.base import ToolError
from agile_mcp.tools.burndown_chart_tool import GetSprintBurndownChartTool


class TestBurndownChartTool:
    """Test cases for burndown chart tool."""

    @pytest.fixture
    def mock_agent(self):
        """Fixture for a mocked agent."""
        agent = MagicMock()
        agent.project_manager.is_initialized.return_value = True
        return agent

    @patch("agile_mcp.tools.burndown_chart_tool.SprintService")
    def test_get_burndown_chart_success(self, mock_sprint_service_class, mock_agent):
        """Test successful retrieval of a burndown chart."""
        # Set up the mock service instance
        mock_sprint_service = MagicMock()
        mock_sprint_service.get_sprint_burndown_data.return_value = {
            "sprint_name": "Sprint 1",
            "total_points": 10,
            "sprint_duration_days": 5,
            "ideal_burn_per_day": 2.0,
            "burndown": [
                {"date": "2025-01-01", "remaining_points": 10, "ideal_points": 10.0},
                {"date": "2025-01-02", "remaining_points": 8, "ideal_points": 8.0},
                {"date": "2025-01-03", "remaining_points": 6, "ideal_points": 6.0},
                {"date": "2025-01-04", "remaining_points": 4, "ideal_points": 4.0},
                {"date": "2025-01-05", "remaining_points": 2, "ideal_points": 2.0},
                {"date": "2025-01-06", "remaining_points": 0, "ideal_points": 0.0},
            ],
        }
        mock_sprint_service_class.return_value = mock_sprint_service

        burndown_tool = GetSprintBurndownChartTool(mock_agent)
        result = burndown_tool.apply(sprint_id="SPRINT-1")

        assert "Generated burndown chart for sprint: Sprint 1" in result.message
        assert "Ideal Burn: 2.00 points/day" in result.data["chart"]
        assert "2025-01-01 | 10               | 10.00" in result.data["chart"]

        mock_sprint_service.get_sprint_burndown_data.assert_called_once_with("SPRINT-1")

    @patch("agile_mcp.tools.burndown_chart_tool.SprintService")
    def test_get_burndown_chart_not_found(self, mock_sprint_service_class, mock_agent):
        """Test retrieving a burndown chart for a non-existent sprint."""
        # Set up the mock service instance to return None
        mock_sprint_service = MagicMock()
        mock_sprint_service.get_sprint_burndown_data.return_value = None
        mock_sprint_service_class.return_value = mock_sprint_service

        burndown_tool = GetSprintBurndownChartTool(mock_agent)

        with pytest.raises(ToolError, match="Could not generate burndown chart for sprint with ID SPRINT-X"):
            burndown_tool.apply(sprint_id="SPRINT-X")

    @patch("agile_mcp.tools.burndown_chart_tool.SprintService")
    def test_get_burndown_chart_empty_data(self, mock_sprint_service_class, mock_agent):
        """Test retrieving a burndown chart when sprint has no data."""
        # Set up the mock service instance to return empty dict
        mock_sprint_service = MagicMock()
        mock_sprint_service.get_sprint_burndown_data.return_value = {}
        mock_sprint_service_class.return_value = mock_sprint_service

        burndown_tool = GetSprintBurndownChartTool(mock_agent)

        with pytest.raises(ToolError, match="Could not generate burndown chart for sprint with ID SPRINT-EMPTY"):
            burndown_tool.apply(sprint_id="SPRINT-EMPTY")

    def test_get_burndown_chart_not_initialized(self, mock_agent):
        """Test retrieval when project is not initialized."""
        mock_agent.project_manager.is_initialized.return_value = False
        mock_agent.project_path = None
        burndown_tool = GetSprintBurndownChartTool(mock_agent)

        with pytest.raises(ToolError, match="No project directory is set"):
            burndown_tool.apply(sprint_id="SPRINT-1")
