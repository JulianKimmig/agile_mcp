"""Tests for base tool functionality."""

import json
import pytest
from unittest.mock import Mock
from typing import Dict, Any

from agile_mcp.tools.base import AgileTool, ToolResult, ToolError


def parse_tool_result(json_result: str) -> Dict[str, Any]:
    """Parse JSON tool result.
    
    Args:
        json_result: JSON string from tool execution
        
    Returns:
        Parsed result dictionary
    """
    return json.loads(json_result)


class TestAgileTool:
    """Test cases for AgileTool base class."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_agent = Mock()

    def test_agile_tool_is_abstract(self) -> None:
        """Test that AgileTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AgileTool(self.mock_agent)
    
    def test_get_name_from_class_name(self) -> None:
        """Test that tool names are derived from class names."""
        class CreateStoryTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = CreateStoryTool(self.mock_agent)
        assert tool.get_name() == "create_story"

    def test_get_name_handles_tool_suffix(self) -> None:
        """Test that 'Tool' suffix is removed from class names."""
        class UpdateTaskTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = UpdateTaskTool(self.mock_agent)
        assert tool.get_name() == "update_task"

    def test_get_description_from_docstring(self) -> None:
        """Test that tool descriptions are extracted from docstrings."""
        class TestTool(AgileTool):
            """This is a test tool for demonstration purposes."""
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        assert tool.get_description() == "This is a test tool for demonstration purposes."

    def test_get_description_returns_default_if_no_docstring(self) -> None:
        """Test that a default description is provided if no docstring exists."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        description = tool.get_description()
        assert "agile project management" in description.lower()

    def test_get_parameters_returns_empty_by_default(self) -> None:
        """Test that get_parameters returns empty dict by default."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        assert tool.get_parameters() == {}

    def test_validate_input_passes_by_default(self) -> None:
        """Test that input validation passes by default."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        # Should not raise any exceptions
        tool.validate_input({"test": "value"})

    def test_format_result_handles_success(self) -> None:
        """Test that successful results are formatted correctly."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        result = tool.format_result("Success message")
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.message == "Success message"
        assert result.data is None

    def test_format_result_handles_data(self) -> None:
        """Test that results with data are formatted correctly."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        test_data = {"id": "STORY-001", "title": "Test Story"}
        result = tool.format_result("Story created", data=test_data)
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.message == "Story created"
        assert result.data == test_data

    def test_format_error_creates_error_result(self) -> None:
        """Test that errors are formatted correctly."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "test"
        
        tool = TestTool(self.mock_agent)
        result = tool.format_error("Something went wrong")
        
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.message == "Something went wrong"
        assert result.data is None

    def test_apply_ex_catches_exceptions(self) -> None:
        """Test that apply_ex catches and formats exceptions."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                raise ValueError("Test error")
        
        tool = TestTool(self.mock_agent)
        json_result = tool.apply_ex(test="value")
        result = parse_tool_result(json_result)
        
        assert result["success"] is False
        assert "Test error" in result["message"]

    def test_apply_ex_validates_input(self) -> None:
        """Test that apply_ex validates input before execution."""
        class TestTool(AgileTool):
            def validate_input(self, params: Dict[str, Any]) -> None:
                if "required" not in params:
                    raise ToolError("Missing required parameter")
            
            def apply(self, **kwargs) -> str:
                return "success"
        
        tool = TestTool(self.mock_agent)
        json_result = tool.apply_ex()
        result = parse_tool_result(json_result)
        
        assert result["success"] is False
        assert "Missing required parameter" in result["message"]

    def test_apply_ex_returns_formatted_success(self) -> None:
        """Test that successful execution is properly formatted."""
        class TestTool(AgileTool):
            def apply(self, **kwargs) -> str:
                return "Operation completed successfully"
        
        tool = TestTool(self.mock_agent)
        json_result = tool.apply_ex(param="value")
        result = parse_tool_result(json_result)
        
        assert result["success"] is True
        assert result["message"] == "Operation completed successfully"


class TestToolResult:
    """Test cases for ToolResult class."""

    def test_tool_result_creation_with_success(self) -> None:
        """Test creating a successful ToolResult."""
        result = ToolResult(success=True, message="Operation successful")
        
        assert result.success is True
        assert result.message == "Operation successful"
        assert result.data is None

    def test_tool_result_creation_with_data(self) -> None:
        """Test creating a ToolResult with data."""
        test_data = {"id": "TEST-001", "value": 42}
        result = ToolResult(success=True, message="Data retrieved", data=test_data)
        
        assert result.success is True
        assert result.message == "Data retrieved"
        assert result.data == test_data

    def test_tool_result_json_serialization(self) -> None:
        """Test that ToolResult can be serialized to JSON."""
        test_data = {"id": "TEST-001", "items": [1, 2, 3]}
        result = ToolResult(success=True, message="Test message", data=test_data)
        
        json_str = result.to_json()
        assert '"success": true' in json_str
        assert '"message": "Test message"' in json_str
        assert '"data"' in json_str
        assert '"id": "TEST-001"' in json_str

    def test_tool_result_string_representation(self) -> None:
        """Test string representation of ToolResult."""
        result = ToolResult(success=True, message="Test message")
        str_repr = str(result)
        
        assert "ToolResult" in str_repr
        assert "success=True" in str_repr
        assert "Test message" in str_repr


class TestToolError:
    """Test cases for ToolError exception."""

    def test_tool_error_creation(self) -> None:
        """Test creating a ToolError exception."""
        error = ToolError("Something went wrong")
        
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)

    def test_tool_error_with_details(self) -> None:
        """Test creating a ToolError with additional details."""
        details = {"field": "title", "reason": "too short"}
        error = ToolError("Validation failed", details=details)
        
        assert str(error) == "Validation failed"
        assert error.details == details

    def test_tool_error_without_details(self) -> None:
        """Test that ToolError works without details."""
        error = ToolError("Simple error")
        
        assert str(error) == "Simple error"
        assert error.details is None 