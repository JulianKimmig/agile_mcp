"""Project management tools for Agile MCP Server."""

import os
from pathlib import Path
from typing import Dict, Any

from .base import AgileTool, ToolError, ToolResult


class SetProjectTool(AgileTool):
    """Set the project directory for the Agile MCP Server."""

    def apply(self, project_path: str) -> ToolResult:
        """Set the project directory for agile project management.

        Args:
            project_path: Path to the project directory (required). Can be relative or absolute.
                         Use '.' for current directory.

        Returns:
            Success message with the resolved project path
        """
        # Validate that project_path is not empty
        if not project_path:
            raise ToolError("Project path cannot be empty")

        # Handle special case for current directory
        if project_path == ".":
            project_path = os.getcwd()

        # Resolve the path to absolute
        resolved_path = Path(project_path).resolve()

        # Check if path exists and is a directory
        if not resolved_path.exists():
            raise ToolError(f"Project path does not exist: {resolved_path}")

        if not resolved_path.is_dir():
            raise ToolError(f"Project path is not a directory: {resolved_path}")

        # Set the project path in the server
        self.agent.set_project_path(str(resolved_path))

        return self.format_result(
            f"Project directory set successfully to: {resolved_path}",
            {"project_path": str(resolved_path)}
        )


class GetProjectTool(AgileTool):
    """Get the current project directory for the Agile MCP Server."""

    def apply(self) -> ToolResult:
        """Get the current project directory.

        Returns:
            Current project directory path or message if not set
        """
        if self.agent.project_path is None:
            return self.format_result(
                "No project directory is currently set. Use set_project to set one first.",
                {"project_path": None}
            )

        return self.format_result(
            f"Current project directory: {self.agent.project_path}",
            {"project_path": self.agent.project_path}
        )
