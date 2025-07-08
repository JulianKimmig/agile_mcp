"""Base classes for Agile MCP tools."""

import json
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp.utilities.func_metadata import FuncMetadata, func_metadata
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..server import AgileMCPServer


class ToolError(Exception):
    """Exception raised by tools for validation or execution errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialize the tool error.

        Args:
            message: Error message
            details: Optional additional error details
        """
        super().__init__(message)
        self.details = details


class ToolResult(BaseModel):
    """Represents the result of a tool execution."""

    success: bool
    message: str
    data: dict[str, Any] | None = Field(None)

    # def __init__(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None):
    #     """Initialize the tool result.

    #     Args:
    #         success: Whether the tool execution was successful
    #         message: Result message
    #         data: Optional data payload
    #     """
    #     self.success = success
    #     self.message = message
    #     self.data = data

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary format.

        Returns:
            Dictionary representation of the result
        """
        result = {"success": self.success, "message": self.message}
        if self.data:
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


class ToolResultError(ToolResult):
    def __init__(self, error: Exception):
        super().__init__(success=False, message=f"Tool Error: {str(error)}")


class AgileTool(ABC):
    """Base class for all Agile MCP tools."""

    def __init__(self, agent: "AgileMCPServer"):
        """Initialize the tool.

        Args:
            agent: The MCP server/agent instance
        """
        self.agent = agent

    @abstractmethod
    def apply(self, *args, **kwargs) -> ToolResult:
        """Apply the tool with given parameters.

        This method must be implemented by subclasses with their specific parameter signatures.
        All tools should return a ToolResult object with success status, message, and optional data.

        Returns:
            ToolResult: Result of the tool execution
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
        if class_name.endswith("Tool"):
            class_name = class_name[:-4]

        # Convert CamelCase to snake_case
        snake_case = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        snake_case = re.sub("([a-z0-9])([A-Z])", r"\1_\2", snake_case).lower()

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
        apply_method = getattr(self.__class__, "apply", None)
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
        apply_method = getattr(self.__class__, "apply", None)
        if apply_method is None:
            raise RuntimeError(f"apply method not defined in {self.__class__}")

        return func_metadata(apply_method, skip_names=["self"])

    def get_parameters(self) -> dict[str, Any]:
        """Get parameter specification for the tool.

        Returns:
            Dictionary containing parameter specifications
        """
        return {}

    def validate_input(self, input_data: dict[str, Any]) -> None:
        """Validate input parameters for the tool.

        Subclasses should override this method to implement specific validation logic.

        Args:
            input_data: The input data to validate

        Raises:
            ToolError: If validation fails
        """
        pass

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

    def format_result(self, message: str, data: dict[str, Any] | None = None) -> ToolResult:
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

    def apply_ex(self, **kwargs: Any) -> ToolResult:
        """Apply the tool with error handling for MCP compatibility.

        This method is required for MCP tool registration and provides
        the standardized interface expected by the MCP system.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult
        """
        try:
            # Validate input parameters
            self.validate_input(kwargs)

            # Execute the tool - now always returns ToolResult
            result = self.apply(**kwargs)

            # Ensure we got a ToolResult
            if not isinstance(result, ToolResult):
                raise ToolError(
                    f"Tool {self.get_name()} apply method must return a ToolResult object, got {type(result)}"
                )

            return result

        except ToolError as e:
            # Handle tool-specific errors
            error_result = ToolResultError(error=e)
            return error_result

        except Exception as e:
            # Handle unexpected errors
            error_result = ToolResultError(error=ToolError(f"Unexpected error in {self.get_name()}: {str(e)}"))
            return error_result

    def _format_message_from_data(self, data: dict[str, Any]) -> str:
        """Format a human-readable message from structured data.

        This method is deprecated and will be removed. Tools should format
        their own messages when creating ToolResult objects.

        Args:
            data: Structured data returned from apply()

        Returns:
            Human-readable message string
        """
        # Default implementation - subclasses should override for better messages
        if isinstance(data, dict):
            if "message" in data:
                return str(data["message"])
            elif "count" in data and "items" in data:
                return f"Found {data['count']} items"
            elif "success" in data:
                return "Operation completed successfully" if data["success"] else "Operation failed"

        return f"Tool {self.get_name()} completed successfully"
