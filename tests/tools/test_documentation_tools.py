"""Tests for documentation tools."""

import pytest
from unittest.mock import MagicMock
import json

from agile_mcp.tools.documentation_tools import GetAgileDocumentationTool
from agile_mcp.tools.base import ToolError


class TestDocumentationTools:
    """Test cases for documentation tools."""

    @pytest.fixture
    def mock_agent(self):
        """Fixture for a mocked agent."""
        agent = MagicMock()
        agent.project_path = None  # Simulate uninitialized project
        agent.project_manager = MagicMock()
        agent.project_manager.is_initialized.return_value = False
        agent.story_service = None
        agent.sprint_service = None
        return agent

    def test_get_agile_documentation_success(self, mock_agent):
        """Test successful retrieval of agile documentation."""
        get_doc_tool = GetAgileDocumentationTool(mock_agent)
        mock_agent.config_service.get_agile_documentation_schema.return_value = {"schema": "test_schema"}
        get_doc_tool._generate_agile_documentation = MagicMock(return_value={
            "metadata": {"version": "1.0.0"},
            "agile_principles": {"manifesto": {"values": [{}], "principles": [{}]}},
            "methodologies": {"scrum": {}},
            "workflow_patterns": [{}],
            "tools": {"categories": [{}]}
        })

        result = get_doc_tool.apply()

        assert result["metadata"] == {"version": "1.0.0"}
        assert "agile_principles" in result
        assert "methodologies" in result
        assert "workflow_patterns" in result
        assert "tools" in result
        # The tool does not call get_agile_documentation_schema directly, it calls _generate_agile_documentation
        # mock_agent.config_service.get_agile_documentation_schema.assert_called_once()

    def test_get_agile_documentation_not_initialized(self, mock_agent):
        """Test retrieval when project is not initialized."""
        mock_agent.project_manager.is_initialized.return_value = False
        mock_agent.project_path = None # Ensure project_path is None for uninitialized state
        get_doc_tool = GetAgileDocumentationTool(mock_agent)

        result = get_doc_tool.apply_ex()
        result_data = json.loads(result)
        assert not result_data["success"]
        assert "No project directory is set" in result_data["message"]