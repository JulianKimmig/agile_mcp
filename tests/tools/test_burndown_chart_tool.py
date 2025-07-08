"""Tests for burndown chart tool."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from agile_mcp.tools.burndown_chart_tool import GetSprintBurndownChartTool
from agile_mcp.tools.base import ToolError


class TestBurndownChartTool:
    """Test cases for burndown chart tool."""

    @pytest.fixture
    def mock_agent(self):
        """Fixture for a mocked agent."""
        agent = MagicMock()
        agent.project_manager.is_initialized.return_value = True
        
        # Mock sprint_service.get_sprint to return a sprint with datetime objects
        mock_sprint = MagicMock(spec=['start_date', 'end_date', 'story_ids'])
        mock_sprint.start_date = datetime(2025, 1, 1)
        mock_sprint.end_date = datetime(2025, 1, 6)
        mock_sprint.story_ids = [] # Add story_ids to avoid errors in total_points calculation
        
        # Mock the subtraction operation to return a real timedelta object
        # Mock the subtraction operation to return a real timedelta object
        mock_sprint.__sub__.return_value = timedelta(days=5)
        
        agent.sprint_service.get_sprint.return_value = mock_sprint
        agent.project_manager.get_story.return_value = MagicMock(points=1) # Mock story points for calculation
        
        return agent

    def test_get_burndown_chart_success(self, mock_agent):
        """Test successful retrieval of a burndown chart."""
        burndown_tool = GetSprintBurndownChartTool(mock_agent)
        
        mock_agent.sprint_service.get_sprint_burndown_data.return_value = {
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
            ]
        }

        result = burndown_tool.apply(sprint_id="SPRINT-1")

        assert "Burndown Chart for Sprint: Sprint 1" in result
        assert "Ideal Burn: 2.00 points/day" in result
        assert "2025-01-01 | 10               | 10.00" in result
        mock_agent.sprint_service.get_sprint_burndown_data.assert_called_once_with("SPRINT-1")

    def test_get_burndown_chart_not_found(self, mock_agent):
        """Test retrieving a burndown chart for a non-existent sprint."""
        burndown_tool = GetSprintBurndownChartTool(mock_agent)
        mock_agent.sprint_service.get_sprint_burndown_data.return_value = None

        with pytest.raises(ToolError, match="Could not generate burndown chart for sprint with ID SPRINT-X"):
            burndown_tool.apply(sprint_id="SPRINT-X")

    def test_get_burndown_chart_not_initialized(self, mock_agent):
        """Test retrieval when project is not initialized."""
        mock_agent.project_manager.is_initialized.return_value = False
        mock_agent.project_path = None
        burndown_tool = GetSprintBurndownChartTool(mock_agent)

        with pytest.raises(ToolError, match="No project directory is set"):
            burndown_tool.apply(sprint_id="SPRINT-1")
