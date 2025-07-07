"""Base classes for Agile MCP tools."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from mcp.server.fastmcp.utilities.func_metadata import FuncMetadata, func_metadata

if TYPE_CHECKING:
    from ..server import AgileMCPServer


class ToolError(Exception):
    """Exception raised by tools for validation or execution errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize the tool error.
        
        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.details = details


class ToolResult:
    """Represents the result of a tool execution."""
    
    def __init__(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None):
        """Initialize the tool result.
        
        Args:
            success: Whether the tool execution was successful
            message: Result message
            data: Optional data payload
        """
        self.success = success
        self.message = message
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format.
        
        Returns:
            Dictionary representation of the result
        """
        result = {
            "success": self.success,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    def to_json(self) -> str:
        """Convert result to JSON string.
        
        Returns:
            JSON string representation of the result
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def __str__(self) -> str:
        """String representation of the result."""
        return f"ToolResult(success={self.success}, message='{self.message}', data={self.data})"


class AgileTool(ABC):
    """Base class for all Agile MCP tools."""
    
    def __init__(self, agent: "AgileMCPServer"):
        """Initialize the tool.
        
        Args:
            agent: The MCP server/agent instance
        """
        self.agent = agent
    
    @abstractmethod
    def apply(self, *args, **kwargs) -> str:
        """Apply the tool with given parameters.
        
        This method must be implemented by subclasses with their specific parameter signatures.
        
        Returns:
            Result message string
        """
        pass
    
    def get_name(self) -> str:
        """Get the tool name from the class name.
        
        Converts CamelCase to snake_case and removes 'Tool' suffix.
        
        Returns:
            Tool name in snake_case
        """
        class_name = self.__class__.__name__
        
        # Remove 'Tool' suffix if present
        if class_name.endswith('Tool'):
            class_name = class_name[:-4]
        
        # Convert CamelCase to snake_case
        snake_case = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case).lower()
        
        return snake_case
    
    def get_description(self) -> str:
        """Get the tool description from the class docstring.
        
        Returns:
            Tool description string
        """
        if self.__class__.__doc__:
            return self.__class__.__doc__.strip()
        else:
            return f"Agile project management tool: {self.get_name()}"
    
    def get_apply_docstring(self) -> str:
        """Get the docstring for the apply method.
        
        This method is required for MCP tool registration.
        
        Returns:
            Apply method docstring
        """
        apply_method = getattr(self.__class__, 'apply', None)
        if apply_method and apply_method.__doc__:
            return apply_method.__doc__.strip()
        else:
            return f"Apply the {self.get_name()} tool."
    
    def get_apply_fn_metadata(self) -> FuncMetadata:
        """Get the metadata for the apply method.
        
        This method is required for MCP tool registration.
        
        Returns:
            FuncMetadata for the apply method
        """
        apply_method = getattr(self.__class__, 'apply', None)
        if apply_method is None:
            raise RuntimeError(f"apply method not defined in {self.__class__}")
        
        return func_metadata(apply_method, skip_names=["self"])
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the tool parameters specification.
        
        Override this method to specify tool parameters.
        
        Returns:
            Dictionary of parameter specifications
        """
        return {}
    
    def validate_input(self, params: Dict[str, Any]) -> None:
        """Validate input parameters.
        
        Override this method to add custom validation.
        
        Args:
            params: Input parameters to validate
            
        Raises:
            ToolError: If validation fails
        """
        pass  # Default implementation does nothing
    
    def _check_project_initialized(self) -> None:
        """Check if the project is initialized and raise error if not.
        
        Raises:
            ToolError: If project is not set or services not initialized
        """
        if self.agent.project_path is None:
            raise ToolError(
                "No project directory is set. Please use the 'set_project' tool to set a project directory first. "
                "Usually this should be set to the current project directory as an absolute path."
            )
        
        if not self.agent.project_manager or not self.agent.story_service or not self.agent.sprint_service:
            raise ToolError(
                "Project services are not initialized. Please use the 'set_project' tool to set a valid project directory first."
            )
    
    def format_result(self, message: str, data: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Format a successful result.
        
        Args:
            message: Success message
            data: Optional data payload
            
        Returns:
            ToolResult object
        """
        return ToolResult(success=True, message=message, data=data)
    
    def format_error(self, message: str) -> ToolResult:
        """Format an error result.
        
        Args:
            message: Error message
            
        Returns:
            ToolResult object
        """
        return ToolResult(success=False, message=message)
    
    def apply_with_error_handling(self, **kwargs: Any) -> ToolResult:
        """Apply the tool with comprehensive error handling.
        
        This method wraps the apply() method with validation and error handling.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            ToolResult object
        """
        try:
            # Validate input parameters
            self.validate_input(kwargs)
            
            # Execute the tool
            result_message = self.apply(**kwargs)
            
            # Return formatted success result
            return self.format_result(result_message)
            
        except ToolError as e:
            # Handle tool-specific errors
            return self.format_error(str(e))
            
        except Exception as e:
            # Handle unexpected errors
            return self.format_error(f"Unexpected error: {str(e)}")
    
    def apply_ex(self, **kwargs: Any) -> str:
        """Apply the tool with error handling for MCP compatibility.
        
        This method is required for MCP tool registration and provides
        the standardized interface expected by the MCP system.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Result string (JSON format for complex results)
        """
        try:
            # Validate input parameters
            self.validate_input(kwargs)
            
            # Execute the tool
            result_message = self.apply(**kwargs)
            
            return result_message
            
        except ToolError as e:
            # Handle tool-specific errors
            return f"Tool Error: {str(e)}"
            
        except Exception as e:
            # Handle unexpected errors
            return f"Unexpected error in {self.get_name()}: {str(e)}" 