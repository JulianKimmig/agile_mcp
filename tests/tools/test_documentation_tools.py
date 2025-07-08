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
        agent.project_path = "/test/project"  # Simulate initialized project
        agent.project_manager = MagicMock()
        agent.project_manager.is_initialized.return_value = True
        agent.story_service = MagicMock()
        agent.sprint_service = MagicMock()
        return agent

    def test_get_agile_documentation_success(self, mock_agent):
        """Test successful retrieval of agile documentation."""
        get_doc_tool = GetAgileDocumentationTool(mock_agent)

        result = get_doc_tool.apply()

        # The result should be a JSON string, parse it to check content
        result_data = json.loads(result)
        assert result_data["metadata"]["version"] == "1.0.0"
        assert "agile_principles" in result_data
        assert "methodologies" in result_data
        assert "workflow_patterns" in result_data
        assert "tools" in result_data

    def test_get_agile_documentation_yaml_format(self, mock_agent):
        """Test retrieval of agile documentation in YAML format."""
        get_doc_tool = GetAgileDocumentationTool(mock_agent)

        result = get_doc_tool.apply(format="yaml")

        # Should be YAML string
        assert "metadata:" in result
        assert "version: 1.0.0" in result

    def test_get_agile_documentation_summary(self, mock_agent):
        """Test retrieval of summary documentation."""
        get_doc_tool = GetAgileDocumentationTool(mock_agent)

        result = get_doc_tool.apply(detail_level="summary")

        result_data = json.loads(result)
        assert result_data["metadata"]["version"] == "1.0.0"
        # Summary should have counts rather than full data
        assert "values_count" in result_data["agile_principles"]["manifesto"]

    def test_get_agile_documentation_specific_topic(self, mock_agent):
        """Test retrieval of specific topic documentation."""
        get_doc_tool = GetAgileDocumentationTool(mock_agent)

        result = get_doc_tool.apply(topic="principles")

        result_data = json.loads(result)
        assert "agile_principles" in result_data
        assert "methodologies" not in result_data

    def test_get_agile_documentation_not_initialized(self, mock_agent):
        """Test retrieval when project is not initialized."""
        mock_agent.project_manager.is_initialized.return_value = False
        mock_agent.project_path = None
        get_doc_tool = GetAgileDocumentationTool(mock_agent)

        result = get_doc_tool.apply_ex()
        result_data = json.loads(result)
        assert result_data["success"] is True  # Documentation doesn't require project initialization