"""Agile MCP Server implementation."""

import logging
import sys
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import docstring_parser
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools.base import Tool as MCPTool
from mcp.server.fastmcp.utilities.func_metadata import FuncMetadata

from .services.config_service import ConfigurationService
from .services.dependency_service import DependencyService
from .services.epic_service import EpicService
from .services.sprint_service import SprintService
from .services.story_service import StoryService
from .services.task_service import TaskService
from .storage.filesystem import AgileProjectManager
from .tools.base import ToolResult
from .tools.burndown_chart_tool import GetSprintBurndownChartTool
from .tools.dependency_tools import (
    AddDependencyTool,
    CheckCanStartTool,
    GetDependenciesTool,
    GetDependencyGraphTool,
    RemoveDependencyTool,
)
from .tools.documentation_tools import GetAgileDocumentationTool
from .tools.epic_tools import (
    CreateEpicTool,
    DeleteEpicTool,
    GetEpicTool,
    GetProductBacklogTool,
    ListEpicsTool,
    ManageEpicStoriesTool,
    UpdateEpicTool,
)
from .tools.overview_tools import GetProjectOverviewTool
from .tools.project_tools import GetProjectTool, SetProjectTool
from .tools.sprint_tools import (
    CreateSprintTool,
    GetActiveSprintTool,
    GetSprintProgressTool,
    GetSprintTool,
    ListSprintsTool,
    ManageSprintStoriesTool,
    UpdateSprintTool,
)
from .tools.story_tools import (
    CreateStoryTool,
    DeleteStoryTool,
    GetStoryTool,
    ListStoriesTool,
    UpdateStoryTool,
)
from .tools.task_tools import (
    CreateTaskTool,
    DeleteTaskTool,
    GetTaskTool,
    ListTasksTool,
    UpdateTaskTool,
)

# Configure logging for MCP
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-5s %(asctime)-15s %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    stream=sys.stderr,  # MCP uses stdio for communication, so log to stderr
)

log = logging.getLogger(__name__)


class AgileToolInterface:
    """Interface for agile tools to be compatible with MCP."""

    def get_name(self) -> str:
        """Get the tool name."""
        ...

    def get_apply_docstring(self) -> str:
        """Get the docstring for the apply method."""
        ...

    def get_apply_fn_metadata(self) -> FuncMetadata:
        """Get the metadata for the apply method."""
        ...

    def apply_ex(self, **kwargs) -> ToolResult:
        """Apply the tool with error handling."""
        ...


class AgileMCPServer:
    """Main MCP server for agile project management."""

    def __init__(self, project_path: str | None = None):
        """Initialize the Agile MCP Server.

        Args:
            project_path: Path to the project directory (optional)
        """
        self.project_path = Path(project_path).resolve() if project_path else None
        self.project_manager: AgileProjectManager | None = None
        self.story_service: StoryService | None = None
        self.sprint_service: SprintService | None = None
        self.task_service: TaskService | None = None
        self.epic_service: EpicService | None = None
        self.config_service: ConfigurationService | None = None
        self.dependency_service: DependencyService | None = None
        self.mcp_server: FastMCP | None = None

        if self.project_path:
            log.info(f"Initializing Agile MCP Server for project: {self.project_path}")
        else:
            log.info("Initializing Agile MCP Server without project directory (use set_project tool to set one)")

    def _initialize_services(self) -> None:
        """Initialize all services and dependencies."""
        if self.project_path is None:
            raise RuntimeError("Project path must be set before initializing services. Use set_project tool first.")

        log.info("Initializing project services...")

        # Initialize project manager and create .agile folder if needed
        self.project_manager = AgileProjectManager(self.project_path)
        self.project_manager.initialize()

        # Initialize configuration service
        self.config_service = ConfigurationService(self.project_manager)

        # Initialize story service
        self.story_service = StoryService(self.project_manager)

        # Initialize sprint service
        self.sprint_service = SprintService(self.project_manager)

        # Initialize task service
        self.task_service = TaskService(self.project_manager)

        # Initialize epic service
        self.epic_service = EpicService(self.project_manager)

        # Initialize dependency service
        self.dependency_service = DependencyService(self.project_manager)

        log.info("Project services initialized successfully")

    def set_project_path(self, project_path: str) -> None:
        """Set the project path and re-initialize services.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        log.info(f"Setting project path to: {self.project_path}")

        # Re-initialize services with new project path
        self._initialize_services()

        # Update tools in MCP server if it exists
        if self.mcp_server is not None:
            self._set_mcp_tools(self.mcp_server)

    def _iter_tools(self) -> Iterator[AgileToolInterface]:
        """Iterate over all available agile tools.

        Returns:
            Iterator of tool instances
        """
        # Project management tools (always available)
        project_tools = [
            SetProjectTool(self),
            GetProjectTool(self),
        ]

        # Documentation tools (always available)
        documentation_tools = [
            GetAgileDocumentationTool(self),
        ]

        # Overview tools (always exposed, but will error if no project is set)
        overview_tools = [
            GetProjectOverviewTool(self),
        ]

        # Dependency tools (always exposed, but will error if no project is set)
        dependency_tools = [
            AddDependencyTool(self),
            RemoveDependencyTool(self),
            GetDependenciesTool(self),
            CheckCanStartTool(self),
            GetDependencyGraphTool(self),
        ]

        # Story, task, epic, and sprint tools (always exposed, but will error if no project is set)
        agile_tools = [
            # Story tools
            CreateStoryTool(self),
            GetStoryTool(self),
            UpdateStoryTool(self),
            ListStoriesTool(self),
            DeleteStoryTool(self),
            # Task tools
            CreateTaskTool(self),
            GetTaskTool(self),
            UpdateTaskTool(self),
            ListTasksTool(self),
            DeleteTaskTool(self),
            # Epic tools
            CreateEpicTool(self),
            GetEpicTool(self),
            UpdateEpicTool(self),
            ListEpicsTool(self),
            DeleteEpicTool(self),
            ManageEpicStoriesTool(self),
            GetProductBacklogTool(self),
            # Sprint tools
            CreateSprintTool(self),
            GetSprintTool(self),
            ListSprintsTool(self),
            UpdateSprintTool(self),
            ManageSprintStoriesTool(self),
            GetSprintProgressTool(self),
            GetActiveSprintTool(self),
            GetSprintBurndownChartTool(self),
        ]

        all_tools = project_tools + documentation_tools + overview_tools + dependency_tools + agile_tools
        log.info(f"Available tools: {[tool.get_name() for tool in all_tools]}")
        yield from all_tools

    @staticmethod
    def make_mcp_tool(tool: AgileToolInterface) -> MCPTool:
        """Convert an agile tool to an MCP tool.

        This follows the same pattern as Serena's SerenaMCPFactory.make_mcp_tool().

        Args:
            tool: The agile tool instance

        Returns:
            MCP tool instance
        """
        func_name = tool.get_name()
        func_doc = tool.get_apply_docstring() or ""
        func_arg_metadata = tool.get_apply_fn_metadata()
        is_async = False
        parameters = func_arg_metadata.arg_model.model_json_schema()

        docstring = docstring_parser.parse(func_doc)

        # Mount the tool description as a combination of the docstring description and
        # the return value description, if it exists.
        if docstring.description:
            func_doc = f"{docstring.description.strip().strip('.')}."
        else:
            func_doc = ""
        if docstring.returns and (docstring_returns_descr := docstring.returns.description):
            # Only add a space before "Returns" if func_doc is not empty
            prefix = " " if func_doc else ""
            func_doc = f"{func_doc}{prefix}Returns {docstring_returns_descr.strip().strip('.')}."

        # Parse the parameter descriptions from the docstring and add pass its description
        # to the parameter schema.
        docstring_params = {param.arg_name: param for param in docstring.params}
        parameters_properties: dict[str, dict[str, Any]] = parameters["properties"]
        for parameter, properties in parameters_properties.items():
            if (param_doc := docstring_params.get(parameter)) and param_doc.description:
                param_desc = f"{param_doc.description.strip().strip('.') + '.'}"
                properties["description"] = param_desc[0].upper() + param_desc[1:]

        def execute_fn(**kwargs) -> str:  # type: ignore
            return tool.apply_ex(**kwargs)

        return MCPTool(
            fn=execute_fn,
            name=func_name,
            description=func_doc,
            parameters=parameters,
            fn_metadata=func_arg_metadata,
            is_async=is_async,
            context_kwarg=None,
            annotations=None,
        )

    def _set_mcp_tools(self, mcp: FastMCP) -> None:
        """Update the tools in the MCP server.

        This follows the same pattern as Serena's SerenaMCPFactory._set_mcp_tools().

        Args:
            mcp: The FastMCP server instance
        """
        if mcp is not None:
            # Clear existing tools
            mcp._tool_manager._tools = {}

            # Register all agile tools
            for tool in self._iter_tools():
                mcp_tool = self.make_mcp_tool(tool)
                mcp._tool_manager._tools[tool.get_name()] = mcp_tool

            tool_names = list(mcp._tool_manager._tools.keys())
            log.info(f"Registered {len(tool_names)} MCP tools: {tool_names}")

    @asynccontextmanager
    async def _server_lifespan(self, mcp_server: FastMCP) -> AsyncIterator[None]:
        """Manage server startup and shutdown lifecycle."""
        log.info("Starting Agile MCP Server lifecycle...")

        try:
            # Initialize services only if project path is set
            if self.project_path is not None:
                self._initialize_services()

            # Register tools with MCP server (includes project tools)
            self._set_mcp_tools(mcp_server)

            log.info("MCP server lifecycle setup complete")
            yield

        except Exception as e:
            log.error(f"Error during server lifecycle: {e}")
            raise
        finally:
            log.info("Shutting down Agile MCP Server...")

    def create_mcp_server(self, host: str = "0.0.0.0", port: int = 8000, transport: str = "stdio") -> FastMCP:
        """Create and configure the FastMCP server.

        Args:
            host: Server host (for SSE transport)
            port: Server port (for SSE transport)
            transport: Transport type (stdio or sse)

        Returns:
            Configured FastMCP server instance
        """
        log.info(f"Creating MCP server with transport: {transport}")

        # Create FastMCP server with lifespan management
        if transport == "stdio":
            self.mcp_server = FastMCP("Agile MCP Server", lifespan=self._server_lifespan)
        else:  # sse
            self.mcp_server = FastMCP("Agile MCP Server", lifespan=self._server_lifespan, host=host, port=port)

        return self.mcp_server

    def start(self, transport: str = "stdio", host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the MCP server.

        Args:
            transport: Transport protocol (stdio or sse)
            host: Server host for SSE transport
            port: Server port for SSE transport
        """
        try:
            server = self.create_mcp_server(host=host, port=port, transport=transport)

            log.info(f"Starting MCP server with {transport} transport")

            if transport == "stdio":
                # For stdio transport, just call run() without parameters
                server.run()
            else:  # sse
                # For sse transport, call run() with transport parameters
                server.run(transport="sse")

        except KeyboardInterrupt:
            log.info("Server stopped by user")
        except Exception as e:
            log.error(f"Server error: {e}")
            raise


# Compatibility class for tools that expect an agent
class AgileAgent:
    """Agent wrapper for backward compatibility with tool interfaces."""

    def __init__(self, server: AgileMCPServer):
        """Initialize the agent.

        Args:
            server: The MCP server instance
        """
        self.server = server
        self.project_manager = server.project_manager
        self.story_service = server.story_service
        self.sprint_service = server.sprint_service
        self.task_service = server.task_service
        self.epic_service = server.epic_service
        self.dependency_service = server.dependency_service
