"""Tests for project management tools."""

import tempfile
import os
from pathlib import Path
import pytest

from agile_mcp.server import AgileMCPServer
from agile_mcp.tools.project_tools import SetProjectTool, GetProjectTool
from agile_mcp.tools.base import ToolError


class TestProjectTools:
    """Test project management tools."""
    
    @pytest.fixture
    def server_without_project(self):
        """Create a server without a project."""
        return AgileMCPServer()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_get_project_tool_no_project_set(self, server_without_project):
        """Test GetProjectTool when no project is set."""
        tool = GetProjectTool(server_without_project)
        result = tool.apply()
        
        assert "No project directory is currently set" in result
        assert "set_project" in result
    
    def test_get_project_tool_with_project_set(self, temp_project_dir):
        """Test GetProjectTool when project is set."""
        server = AgileMCPServer(str(temp_project_dir))
        tool = GetProjectTool(server)
        result = tool.apply()
        
        assert "Current project directory:" in result
        # Check that the resolved path is in the result
        assert str(temp_project_dir.resolve()) in result
    
    def test_set_project_tool_valid_directory(self, server_without_project, temp_project_dir):
        """Test SetProjectTool with a valid directory."""
        tool = SetProjectTool(server_without_project)
        result = tool.apply(project_path=str(temp_project_dir))
        
        assert "Project directory set successfully" in result
        assert str(temp_project_dir.resolve()) in result
        assert server_without_project.project_path == temp_project_dir.resolve()
        assert server_without_project.project_manager is not None
        assert server_without_project.story_service is not None
        assert server_without_project.sprint_service is not None
    
    def test_set_project_tool_current_directory(self, server_without_project):
        """Test SetProjectTool with current directory."""
        tool = SetProjectTool(server_without_project)
        result = tool.apply(project_path=".")
        
        assert "Project directory set successfully" in result
        expected_path = Path(os.getcwd()).resolve()
        assert server_without_project.project_path == expected_path
    
    def test_set_project_tool_missing_parameter(self, server_without_project):
        """Test SetProjectTool with missing project_path parameter."""
        tool = SetProjectTool(server_without_project)
        
        # The apply method now has a required parameter, so this should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            tool.apply()  # Missing required positional argument
        
        assert "missing 1 required positional argument: 'project_path'" in str(exc_info.value)
    
    def test_set_project_tool_empty_path(self, server_without_project):
        """Test SetProjectTool with empty project path."""
        tool = SetProjectTool(server_without_project)
        
        with pytest.raises(ToolError) as exc_info:
            tool.apply(project_path="")  # Empty string should trigger validation error
        
        assert "Project path cannot be empty" in str(exc_info.value)
    
    def test_set_project_tool_nonexistent_path(self, server_without_project):
        """Test SetProjectTool with nonexistent path."""
        tool = SetProjectTool(server_without_project)
        
        with pytest.raises(ToolError) as exc_info:
            tool.apply(project_path="/nonexistent/path/that/does/not/exist")
        
        assert "Project path does not exist" in str(exc_info.value)
    
    def test_set_project_tool_file_not_directory(self, server_without_project, temp_project_dir):
        """Test SetProjectTool with a file instead of directory."""
        # Create a temporary file
        temp_file = temp_project_dir / "test_file.txt"
        temp_file.write_text("test content")
        
        tool = SetProjectTool(server_without_project)
        
        with pytest.raises(ToolError) as exc_info:
            tool.apply(project_path=str(temp_file))
        
        assert "Project path is not a directory" in str(exc_info.value)
    
    def test_project_tools_get_name(self, server_without_project):
        """Test that tools have correct names."""
        set_tool = SetProjectTool(server_without_project)
        get_tool = GetProjectTool(server_without_project)
        
        assert set_tool.get_name() == "set_project"
        assert get_tool.get_name() == "get_project"
    
    def test_set_project_tool_with_error_handling(self, server_without_project, temp_project_dir):
        """Test SetProjectTool with error handling wrapper."""
        tool = SetProjectTool(server_without_project)
        result = tool.apply_with_error_handling(project_path=str(temp_project_dir))
        
        assert result.success is True
        assert "Project directory set successfully" in result.message
        assert server_without_project.project_path == temp_project_dir.resolve()
    
    def test_set_project_tool_error_handling_invalid_path(self, server_without_project):
        """Test SetProjectTool error handling with invalid path."""
        tool = SetProjectTool(server_without_project)
        result = tool.apply_with_error_handling(project_path="/invalid/path")
        
        assert result.success is False
        assert "Project path does not exist" in result.message 