"""Tests for MCP server integration."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from agile_mcp.server import AgileMCPServer


class TestMCPServerIntegration:
    """Test cases for MCP server integration."""

    @pytest.fixture
    def mock_mcp(self) -> MagicMock:
        """Create a mock MCP object."""
        mock_mcp = MagicMock()
        mock_mcp._tool_manager = MagicMock()
        mock_mcp._tool_manager._tools = {}
        return mock_mcp

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for test project
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir()

        # Initialize server
        self.server = AgileMCPServer(str(self.project_path))

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_server_initialization(self) -> None:
        """Test that server initializes correctly."""
        # Use resolve() to normalize paths for comparison
        assert self.server.project_path.resolve() == self.project_path.resolve()
        assert self.server.project_manager is None
        assert self.server.story_service is None
        assert self.server.mcp_server is None

    def test_service_initialization(self) -> None:
        """Test that services are initialized correctly."""
        self.server._initialize_services()

        assert self.server.project_manager is not None
        assert self.server.story_service is not None

        # Check that .agile folder was created
        agile_folder = self.project_path / ".agile"
        assert agile_folder.exists()
        assert agile_folder.is_dir()

    def test_tool_iteration(self) -> None:
        """Test that tools are properly iterated."""
        self.server._initialize_services()
        tools = list(self.server._iter_tools())

        assert (
            len(tools) == 28
        )  # We have 2 project tools + 1 documentation tool + 5 story tools + 5 task tools + 7 epic tools + 7 sprint tools + 1 burndown chart tool
        tool_names = [tool.get_name() for tool in tools]

        # Check for project tools
        project_tools = ["set_project", "get_project"]
        for name in project_tools:
            assert name in tool_names

        # Check for story tools
        story_tools = ["create_story", "get_story", "update_story", "list_stories", "delete_story"]
        for name in story_tools:
            assert name in tool_names

        # Check for sprint tools
        sprint_tools = [
            "create_sprint",
            "get_sprint",
            "list_sprints",
            "update_sprint",
            "manage_sprint_stories",
            "get_sprint_progress",
            "get_active_sprint",
        ]
        for name in sprint_tools:
            assert name in tool_names

        # Check for documentation tools
        documentation_tools = ["get_agile_documentation"]
        for name in documentation_tools:
            assert name in tool_names

    def test_tool_interface_compliance(self) -> None:
        """Test that tools implement the required interface."""
        self.server._initialize_services()
        tools = list(self.server._iter_tools())

        for tool in tools:
            # Check that each tool has required methods
            assert hasattr(tool, "get_name")
            assert hasattr(tool, "get_apply_docstring")
            assert hasattr(tool, "get_apply_fn_metadata")
            assert hasattr(tool, "apply_ex")

            # Check that methods work
            assert isinstance(tool.get_name(), str)
            assert isinstance(tool.get_apply_docstring(), str)
            assert tool.get_apply_fn_metadata() is not None

    def test_make_mcp_tool(self) -> None:
        """Test conversion of agile tool to MCP tool."""
        self.server._initialize_services()
        tools = list(self.server._iter_tools())
        create_tool = next(tool for tool in tools if tool.get_name() == "create_story")

        mcp_tool = self.server.make_mcp_tool(create_tool)

        # Check MCP tool properties
        assert mcp_tool.name == "create_story"
        assert mcp_tool.description is not None
        assert mcp_tool.parameters is not None
        assert callable(mcp_tool.fn)

    @patch("agile_mcp.server.FastMCP")
    def test_set_mcp_tools(self, mock_fastmcp) -> None:
        """Test setting tools in MCP server."""
        # Setup mock MCP server
        mock_mcp = MagicMock()
        mock_mcp._tool_manager = MagicMock()
        mock_mcp._tool_manager._tools = {}

        self.server._initialize_services()
        self.server._set_mcp_tools(mock_mcp)

        # Check that tools were registered
        assert len(mock_mcp._tool_manager._tools) == 28
        tool_names = list(mock_mcp._tool_manager._tools.keys())

        # Check for project tools
        project_tools = ["set_project", "get_project"]
        for name in project_tools:
            assert name in tool_names

        # Check for story tools
        story_tools = ["create_story", "get_story", "update_story", "list_stories", "delete_story"]
        for name in story_tools:
            assert name in tool_names

        # Check for sprint tools
        sprint_tools = [
            "create_sprint",
            "get_sprint",
            "list_sprints",
            "update_sprint",
            "manage_sprint_stories",
            "get_sprint_progress",
            "get_active_sprint",
        ]
        for name in sprint_tools:
            assert name in tool_names

    def test_create_mcp_server_stdio(self) -> None:
        """Test creating MCP server with stdio transport."""
        with patch("agile_mcp.server.FastMCP") as mock_fastmcp:
            mock_server = MagicMock()
            mock_fastmcp.return_value = mock_server

            result = self.server.create_mcp_server(transport="stdio")

            assert result == mock_server
            mock_fastmcp.assert_called_once()
            # Check that the lifespan parameter was passed
            args, kwargs = mock_fastmcp.call_args
            assert "lifespan" in kwargs

    def test_create_mcp_server_sse(self) -> None:
        """Test creating MCP server with SSE transport."""
        with patch("agile_mcp.server.FastMCP") as mock_fastmcp:
            mock_server = MagicMock()
            mock_fastmcp.return_value = mock_server

            result = self.server.create_mcp_server(transport="sse", host="localhost", port=9000)

            assert result == mock_server
            mock_fastmcp.assert_called_once()
            # Check that host and port were passed
            args, kwargs = mock_fastmcp.call_args
            assert "host" in kwargs
            assert "port" in kwargs

    @pytest.mark.asyncio
    async def test_server_lifespan(self, mock_mcp: MagicMock) -> None:
        """Test server lifespan management."""
        mock_mcp = MagicMock()
        mock_mcp._tool_manager = MagicMock()
        mock_mcp._tool_manager._tools = {}

        # Test the lifespan context manager
        async with self.server._server_lifespan(mock_mcp):
            # Check that services were initialized
            assert self.server.project_manager is not None
            assert self.server.story_service is not None
            assert self.server.sprint_service is not None

            # Check that tools were set
            assert len(mock_mcp._tool_manager._tools) == 28

    def test_tool_error_handling(self) -> None:
        """Test that tools handle errors properly."""
        self.server._initialize_services()
        tools = list(self.server._iter_tools())
        create_tool = next(tool for tool in tools if tool.get_name() == "create_story")

        # Test with missing required parameters
        result = create_tool.apply_ex()  # No parameters provided
        assert "Unexpected error" in result.message or "missing" in result.message

    def test_tool_success_execution(self) -> None:
        """Test successful tool execution."""
        self.server._initialize_services()
        tools = list(self.server._iter_tools())
        create_tool = next(tool for tool in tools if tool.get_name() == "create_story")

        # Test with valid parameters
        result = create_tool.apply_ex(title="Test Story", description="This is a test story", priority="medium")

        assert result.success
        assert "created successfully" in result.message or "Test Story" in result.message

    def test_start_server_stdio(self) -> None:
        """Test starting server with stdio transport."""
        with patch.object(self.server, "create_mcp_server") as mock_create:
            mock_server = MagicMock()
            mock_server.run = MagicMock()
            mock_create.return_value = mock_server

            self.server.start(transport="stdio")

            mock_create.assert_called_once_with(host="0.0.0.0", port=8000, transport="stdio")
            mock_server.run.assert_called_once()

    def test_start_server_sse(self) -> None:
        """Test starting server with SSE transport."""
        with patch.object(self.server, "create_mcp_server") as mock_create:
            mock_server = MagicMock()
            mock_server.run = MagicMock()
            mock_create.return_value = mock_server

            self.server.start(transport="sse", host="localhost", port=9000)

            mock_create.assert_called_once_with(host="localhost", port=9000, transport="sse")
            mock_server.run.assert_called_once_with(transport="sse")

    def test_integration_with_real_tools(self) -> None:
        """Test integration with actual tool implementations."""
        self.server._initialize_services()

        # Create a story using the service directly
        story = self.server.story_service.create_story(
            title="Integration Test Story", description="This story tests the integration"
        )

        # Now try to retrieve it using the tool
        tools = list(self.server._iter_tools())
        get_tool = next(tool for tool in tools if tool.get_name() == "get_story")

        result = get_tool.apply_ex(story_id=story.id)

        assert "Integration Test Story" in result.message
        assert story.id in result.message
