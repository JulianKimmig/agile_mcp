"""Main entry point for the Agile MCP Server."""

import logging
import sys
from pathlib import Path

import click

from .server import AgileMCPServer

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-5s %(asctime)-15s %(name)s - %(message)s",
    stream=sys.stderr
)

log = logging.getLogger(__name__)


def _display_connection_info(transport: str, host: str, port: int, project_path: Path | None) -> None:
    """Display information about how to connect to the MCP server."""
    print("\n" + "=" * 70, file=sys.stderr)
    print("🚀 Agile MCP Server Ready!", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    print(f"\n📡 Transport: {transport.upper()}", file=sys.stderr)
    
    if transport == "stdio":
        print("📋 Connection Method: Standard I/O", file=sys.stderr)
        print("\n🔧 How to connect:", file=sys.stderr)
        print("   This server uses STDIO transport for direct LLM integration.", file=sys.stderr)
        print("   Configure your MCP client with these settings:", file=sys.stderr)
        print("\n   Claude Desktop Configuration:", file=sys.stderr)
        print("   {", file=sys.stderr)
        print('     "mcpServers": {', file=sys.stderr)
        print('       "agile-mcp": {', file=sys.stderr)
        print('         "command": "uv",', file=sys.stderr)
        print('         "args": [', file=sys.stderr)
        if project_path:
            print('           "run", "python", "-m", "agile_mcp",', file=sys.stderr)
            print(f'           "--project", "{project_path}"', file=sys.stderr)
        else:
            print('           "run", "python", "-m", "agile_mcp"', file=sys.stderr)
        print('         ],', file=sys.stderr)
        print('         "cwd": "/path/to/agile-mcp"', file=sys.stderr)
        print('       }', file=sys.stderr)
        print('     }', file=sys.stderr)
        print('   }', file=sys.stderr)
        
    else:  # sse
        print(f"🌐 Server URL: http://{host}:{port}", file=sys.stderr)
        print("\n🔧 How to connect:", file=sys.stderr)
        print("   This server uses SSE (Server-Sent Events) transport.", file=sys.stderr)
        print("   Connect your MCP client to the URL above.", file=sys.stderr)
        print(f"   You can also test it in a browser: http://{host}:{port}", file=sys.stderr)
    
    print(f"\n📁 Project Directory: {project_path or 'Not set (use set_project tool)'}", file=sys.stderr)
    print("🛠️  Available Tools: 14 agile project management tools", file=sys.stderr)
    print("   • 2 Project tools: set_project, get_project", file=sys.stderr)
    print("   • 5 Story tools: create_story, get_story, update_story, list_stories, delete_story", file=sys.stderr)
    print("   • 7 Sprint tools: create_sprint, get_sprint, list_sprints, update_sprint,", file=sys.stderr)
    print("     manage_sprint_stories, get_sprint_progress, get_active_sprint", file=sys.stderr)
    
    if not project_path:
        print("\n⚠️  Note: No project directory set. Use the 'set_project' tool to set one.", file=sys.stderr)
        print("   Agile tools will error until a project directory is configured.", file=sys.stderr)
    
    print("\n💡 Need help? Check the README.md for more integration examples.", file=sys.stderr)
    print("🛑 Press Ctrl+C to stop the server\n", file=sys.stderr)
    print("=" * 70, file=sys.stderr)


@click.command()
@click.option(
    "--project",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the project directory where the .agile folder will be created (optional - can be set later using set_project tool)"
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport protocol for MCP communication (default: stdio)"
)
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host address for SSE transport (default: 0.0.0.0)"
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port for SSE transport (default: 8000)"
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Log level (default: INFO)"
)
@click.version_option(version="0.1.0", message="Agile MCP Server %(version)s")
def main(
    project: Path | None,
    transport: str,
    host: str,
    port: int,
    log_level: str
) -> None:
    """Start the Agile MCP Server.
    
    The Agile MCP Server transforms Large Language Models into powerful agile
    project management assistants. It creates and manages a .agile folder
    structure in your project directory to store all agile artifacts.
    
    You can start the server without specifying a project directory and set it
    later using the set_project tool, which should typically be set to the
    current project directory as an absolute path.
    
    Examples:
        agile-mcp-server
        agile-mcp-server --project /path/to/project
        agile-mcp-server --project . --transport sse --port 9000
    """
    try:
        # Configure logging level
        numeric_level = getattr(logging, log_level.upper())
        logging.getLogger().setLevel(numeric_level)
        
        # Resolve project path if provided
        project_path = project.resolve() if project else None
        
        if project_path:
            log.info(f"Starting Agile MCP Server for project: {project_path}")
        else:
            log.info("Starting Agile MCP Server without project directory (use set_project tool to set one)")
        
        log.info(f"Transport: {transport}")
        
        if transport == "sse":
            log.info(f"Server will be available at http://{host}:{port}")
        
        # Create the server
        server = AgileMCPServer(str(project_path) if project_path else None)
        
        # Display connection information
        _display_connection_info(transport, host, port, project_path)
        
        # Start the server
        server.start(transport=transport, host=host, port=port)
        
    except KeyboardInterrupt:
        log.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        log.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 