"""Integration tests for the Agile MCP Server."""

import asyncio
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from agile_mcp.server import AgileMCPServer
from agile_mcp.storage.filesystem import AgileProjectManager


class TestServerIntegration:
    """Test the complete MCP server integration."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_server_initialization(self, temp_project_dir):
        """Test that the server initializes correctly."""
        server = AgileMCPServer(str(temp_project_dir))
        
        assert server.project_path == temp_project_dir.resolve()
        assert server.project_manager is None  # Not initialized yet
        assert server.story_service is None  # Not initialized yet
        assert server.mcp_server is None  # Not created yet
    
    def test_server_initialization_without_project(self):
        """Test that the server initializes correctly without a project directory."""
        server = AgileMCPServer()
        
        assert server.project_path is None
        assert server.project_manager is None  # Not initialized yet
        assert server.story_service is None  # Not initialized yet
        assert server.mcp_server is None  # Not created yet
    
    def test_server_services_initialization(self, temp_project_dir):
        """Test that server services initialize correctly."""
        server = AgileMCPServer(str(temp_project_dir))
        server._initialize_services()
        
        assert server.project_manager is not None
        assert isinstance(server.project_manager, AgileProjectManager)
        assert server.story_service is not None
        
        # Check that .agile directory was created
        agile_dir = temp_project_dir / ".agile"
        assert agile_dir.exists()
        assert agile_dir.is_dir()
    
    def test_server_set_project_path(self, temp_project_dir):
        """Test setting project path after server initialization."""
        server = AgileMCPServer()  # Start without project
        
        # Initially no project path
        assert server.project_path is None
        assert server.project_manager is None
        
        # Set project path
        server.set_project_path(str(temp_project_dir))
        
        # Verify project path was set and services initialized
        assert server.project_path == temp_project_dir.resolve()
        assert server.project_manager is not None
        assert server.story_service is not None
        assert server.sprint_service is not None
    
    def test_server_tools_registration(self, temp_project_dir):
        """Test that tools are registered correctly."""
        server = AgileMCPServer(str(temp_project_dir))
        server._initialize_services()
        
        # Get tools
        tools = list(server._iter_tools())
        
        assert len(tools) == 28  # All story, sprint, project, epic, task, and documentation tools
        tool_names = [tool.get_name() for tool in tools]
        
        # Story tools
        expected_story_tools = [
            "create_story",
            "get_story", 
            "update_story",
            "list_stories",
            "delete_story"
        ]
        
        # Sprint tools
        expected_sprint_tools = [
            "create_sprint",
            "get_sprint",
            "list_sprints",
            "update_sprint",
            "manage_sprint_stories",
            "get_sprint_progress",
            "get_active_sprint"
        ]
        
        # Project tools
        expected_project_tools = [
            "set_project",
            "get_project"
        ]
        
        # Documentation tools
        expected_documentation_tools = [
            "get_agile_documentation"
        ]
        
        expected_tools = expected_story_tools + expected_sprint_tools + expected_project_tools + expected_documentation_tools
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_server_tools_without_project(self):
        """Test that all tools are available when no project is set, but agile tools will error."""
        server = AgileMCPServer()  # Start without project
        
        # Get tools (should include all tools)
        tools = list(server._iter_tools())
        
        assert len(tools) == 28  # All tools should be available
        tool_names = [tool.get_name() for tool in tools]
        
        # Project tools should be available
        assert "set_project" in tool_names
        assert "get_project" in tool_names
        
        # Story and sprint tools should also be available (but will error when called)
        assert "create_story" in tool_names
        assert "create_sprint" in tool_names
        
        # Test that agile tools throw proper error when no project is set
        from agile_mcp.tools.story_tools import CreateStoryTool
        from agile_mcp.tools.base import ToolError
        
        story_tool = CreateStoryTool(server)
        try:
            story_tool.apply(title="Test", description="Test")
            assert False, "Should have thrown an error"
        except ToolError as e:
            assert "No project directory is set" in str(e)
            assert "set_project" in str(e)
    
    def test_mcp_server_creation_stdio(self, temp_project_dir):
        """Test MCP server creation with stdio transport."""
        server = AgileMCPServer(str(temp_project_dir))
        
        mcp_server = server.create_mcp_server(transport="stdio")
        
        assert mcp_server is not None
        assert server.mcp_server is mcp_server
        assert mcp_server.name == "Agile MCP Server"
    
    def test_mcp_server_creation_sse(self, temp_project_dir):
        """Test MCP server creation with SSE transport."""
        server = AgileMCPServer(str(temp_project_dir))
        
        mcp_server = server.create_mcp_server(transport="sse", host="127.0.0.1", port=9999)
        
        assert mcp_server is not None
        assert server.mcp_server is mcp_server
        assert mcp_server.name == "Agile MCP Server"
    
    def test_make_mcp_tool(self, temp_project_dir):
        """Test converting agile tools to MCP tools."""
        from agile_mcp.tools.story_tools import CreateStoryTool
        
        server = AgileMCPServer(str(temp_project_dir))
        server._initialize_services()
        
        agile_tool = CreateStoryTool(server)
        mcp_tool = server.make_mcp_tool(agile_tool)
        
        assert mcp_tool is not None
        assert mcp_tool.name == "create_story"
        assert mcp_tool.description is not None
        assert mcp_tool.parameters is not None
        assert "properties" in mcp_tool.parameters
        # The parameters are now explicit, not wrapped in kwargs
        properties = mcp_tool.parameters["properties"]
        assert "title" in properties
        assert "description" in properties
    
    @pytest.mark.asyncio
    async def test_server_lifespan(self, temp_project_dir):
        """Test server lifespan context manager."""
        from mcp.server.fastmcp import FastMCP
        
        server = AgileMCPServer(str(temp_project_dir))
        mcp_server = FastMCP("Test Server")
        
        # Test that lifespan works without errors
        async with server._server_lifespan(mcp_server):
            # Should have initialized services if project was provided
            if server.project_path:
                assert server.project_manager is not None
                assert server.story_service is not None
                assert server.sprint_service is not None
            
            # Should have registered all tools regardless of project status
            assert len(mcp_server._tool_manager._tools) == 28
            
            # Verify specific story tools exist
            assert "create_story" in mcp_server._tool_manager._tools
            assert "get_story" in mcp_server._tool_manager._tools
            assert "list_stories" in mcp_server._tool_manager._tools
            
            # Verify specific sprint tools exist
            assert "create_sprint" in mcp_server._tool_manager._tools
            assert "get_sprint" in mcp_server._tool_manager._tools
            assert "list_sprints" in mcp_server._tool_manager._tools
            
            # Verify specific project tools exist
            assert "set_project" in mcp_server._tool_manager._tools
            assert "get_project" in mcp_server._tool_manager._tools
            
            # Verify documentation tools exist
            assert "get_agile_documentation" in mcp_server._tool_manager._tools
    
    @pytest.mark.asyncio
    async def test_server_lifespan_without_project(self):
        """Test server lifespan context manager without project directory."""
        from mcp.server.fastmcp import FastMCP
        
        server = AgileMCPServer()  # No project directory
        mcp_server = FastMCP("Test Server")
        
        # Test that lifespan works without errors even without project
        async with server._server_lifespan(mcp_server):
            # Services should not be initialized
            assert server.project_manager is None
            assert server.story_service is None
            assert server.sprint_service is None
            
            # Should still have registered all tools
            assert len(mcp_server._tool_manager._tools) == 28
            
            # Verify project tools exist
            assert "set_project" in mcp_server._tool_manager._tools
            assert "get_project" in mcp_server._tool_manager._tools
            
            # Verify documentation tools exist
            assert "get_agile_documentation" in mcp_server._tool_manager._tools
            
            # Verify agile tools also exist
            assert "create_story" in mcp_server._tool_manager._tools
            assert "create_sprint" in mcp_server._tool_manager._tools
    
    def test_server_command_line_interface(self, temp_project_dir):
        """Test that the server can be started from command line."""
        # Test that the CLI starts without immediate errors
        cmd = [
            "uv", "run", "python", "-m", "agile_mcp",
            "--project", str(temp_project_dir),
            "--log-level", "ERROR"  # Reduce noise in tests
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Give it a moment to start and potentially fail
            time.sleep(0.5)
            
            # Check if process is still running (it should be waiting for MCP input)
            poll_result = process.poll()
            
            if poll_result is not None:
                # Process exited, check for errors
                stdout, stderr = process.communicate()
                if poll_result != 0:
                    pytest.fail(f"Server failed to start. Exit code: {poll_result}, stderr: {stderr}")
            
            # Process is running, which means it started successfully
            assert process.poll() is None, "Server should be running and waiting for input"
            
        finally:
            # Clean up the process
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    
    def test_server_command_line_interface_without_project(self):
        """Test that the server can be started from command line without a project directory."""
        # Test that the CLI starts without immediate errors when no project is specified
        cmd = [
            "uv", "run", "python", "-m", "agile_mcp",
            "--log-level", "ERROR"  # Reduce noise in tests
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Give it a moment to start and potentially fail
            time.sleep(0.5)
            
            # Check if process is still running (it should be waiting for MCP input)
            poll_result = process.poll()
            
            if poll_result is not None:
                # Process exited, check for errors
                stdout, stderr = process.communicate()
                if poll_result != 0:
                    pytest.fail(f"Server failed to start. Exit code: {poll_result}, stderr: {stderr}")
            
            # Process is running, which means it started successfully
            assert process.poll() is None, "Server should be running and waiting for input"
            
        finally:
            # Clean up the process
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    
    def test_agile_agent_compatibility(self, temp_project_dir):
        """Test that AgileAgent provides backward compatibility."""
        from agile_mcp.server import AgileAgent
        
        server = AgileMCPServer(str(temp_project_dir))
        server._initialize_services()
        
        agent = AgileAgent(server)
        
        assert agent.server is server
        assert agent.project_manager is server.project_manager
        assert agent.story_service is server.story_service
        assert agent.sprint_service is server.sprint_service
    
    def test_tool_interface_compliance(self, temp_project_dir):
        """Test that all tools implement the required interface."""
        server = AgileMCPServer(str(temp_project_dir))
        server._initialize_services()
        
        for tool in server._iter_tools():
            # Each tool should implement the AgileToolInterface
            assert hasattr(tool, 'get_name')
            assert hasattr(tool, 'get_apply_docstring')
            assert hasattr(tool, 'get_apply_fn_metadata')
            assert hasattr(tool, 'apply_ex')
            
            # Each method should return the expected types
            name = tool.get_name()
            assert isinstance(name, str)
            assert len(name) > 0
            
            docstring = tool.get_apply_docstring()
            assert isinstance(docstring, str)
            
            metadata = tool.get_apply_fn_metadata()
            assert metadata is not None
            
            # apply_ex should be callable
            assert callable(tool.apply_ex)
    
    def test_error_handling_server_startup(self):
        """Test error handling when server startup fails."""
        # Test with invalid project path
        with pytest.raises(Exception):
            server = AgileMCPServer("/nonexistent/path/that/cannot/be/created")
            server._initialize_services()
    
    def test_server_logging_configuration(self, temp_project_dir):
        """Test that server logging is configured correctly."""
        import logging
        
        server = AgileMCPServer(str(temp_project_dir))
        
        # Check that logging is configured
        logger = logging.getLogger("agile_mcp.server")
        assert logger.level <= logging.INFO  # Should be at INFO level or lower
        
        # Should be able to log without errors
        logger.info("Test log message")
    
    def test_multiple_server_instances(self, temp_project_dir):
        """Test that multiple server instances can coexist."""
        # Create two server instances
        server1 = AgileMCPServer(str(temp_project_dir))
        server2 = AgileMCPServer(str(temp_project_dir))
        
        # Initialize both
        server1._initialize_services()
        server2._initialize_services()
        
        # Both should work independently
        assert server1.project_manager is not None
        assert server2.project_manager is not None
        assert server1.story_service is not None
        assert server2.story_service is not None
        
        # They should operate on the same project directory
        assert server1.project_path == server2.project_path 