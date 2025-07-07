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


@click.group()
@click.version_option(version="0.1.0", message="Agile MCP Server %(version)s")
def cli() -> None:
    """Agile MCP Server - Transform LLMs into powerful agile project management assistants."""
    pass


@cli.command()
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
def start(
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


@cli.command()
@click.option(
    "--project",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the project directory to validate"
)
def validate(project: Path) -> None:
    """Validate the .agile directory for broken references and report them.
    
    This command scans the .agile directory for broken references between
    artifacts (e.g., stories referenced in sprints that no longer exist)
    and reports any issues found.
    """
    try:
        from .storage.filesystem import AgileProjectManager
        
        project_path = project.resolve()
        print(f"🔍 Validating agile project at: {project_path}")
        
        # Check if .agile directory exists
        agile_dir = project_path / ".agile"
        if not agile_dir.exists():
            print("❌ No .agile directory found. This doesn't appear to be an agile project.")
            sys.exit(1)
        
        # Initialize project manager
        project_manager = AgileProjectManager(project_path)
        project_manager.initialize()
        
        print("\n📊 Validation Results:")
        print("-" * 50)
        
        # Validate sprints and their story references
        sprints = project_manager.list_sprints()
        stories = project_manager.list_stories()
        tasks = project_manager.list_tasks()
        
        story_ids = {story.id for story in stories}
        broken_references = []
        
        print(f"📈 Found {len(sprints)} sprints, {len(stories)} stories, {len(tasks)} tasks")
        
        # Check sprint -> story references
        for sprint in sprints:
            broken_story_refs = []
            for story_id in sprint.story_ids:
                if story_id not in story_ids:
                    broken_story_refs.append(story_id)
            
            if broken_story_refs:
                broken_references.append({
                    "type": "sprint_story_reference",
                    "sprint_id": sprint.id,
                    "broken_story_ids": broken_story_refs
                })
        
        # Check task -> story references  
        for task in tasks:
            if task.story_id and task.story_id not in story_ids:
                broken_references.append({
                    "type": "task_story_reference", 
                    "task_id": task.id,
                    "broken_story_id": task.story_id
                })
        
        # Report results
        if not broken_references:
            print("✅ No broken references found. Project is healthy!")
        else:
            print(f"⚠️  Found {len(broken_references)} broken references:")
            
            for ref in broken_references:
                if ref["type"] == "sprint_story_reference":
                    print(f"   • Sprint {ref['sprint_id']} references non-existent stories: {', '.join(ref['broken_story_ids'])}")
                elif ref["type"] == "task_story_reference":
                    print(f"   • Task {ref['task_id']} references non-existent story: {ref['broken_story_id']}")
            
            print(f"\n💡 Tip: These broken references will be automatically cleaned up when you access the affected artifacts.")
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--project",
    required=False,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the project directory (default: current directory)"
)
def status(project: Path | None) -> None:
    """Show project status and summary information.
    
    Displays an overview of the current agile project including configuration,
    sprint progress, story counts, and recent activity.
    """
    try:
        from .storage.filesystem import AgileProjectManager
        from .services.project_status_service import ProjectStatusService
        
        # Use current directory if not specified
        project_path = project.resolve() if project else Path.cwd()
        
        print(f"📊 Agile Project Status: {project_path.name}")
        print("=" * 60)
        
        # Check if .agile directory exists
        agile_dir = project_path / ".agile"
        if not agile_dir.exists():
            print("❌ No .agile directory found. This is not an agile project.")
            print("💡 Run 'agile-mcp-server start --project .' to initialize.")
            sys.exit(1)
        
        # Initialize project manager and status service
        project_manager = AgileProjectManager(project_path)
        project_manager.initialize()
        
        status_service = ProjectStatusService(project_manager)
        summary = status_service.get_project_summary()
        
        # Project Configuration
        print("\n🛠️  Configuration")
        print("-" * 20)
        project_config = summary["project_config"]
        agile_config = summary["agile_config"]
        
        if not project_config["available"]:
            print(f"❌ Configuration error: {project_config.get('error', 'Unknown error')}")
        
        print(f"Project Name:      {project_config['name']}")
        print(f"Version:           {project_config['version']}")
        print(f"Methodology:       {agile_config['methodology']}")
        print(f"Sprint Duration:   {agile_config['sprint_duration_weeks']} weeks")
        print(f"Story Points:      {agile_config['story_point_scale']}")
        
        # Story Statistics
        print("\n📖 Stories")
        print("-" * 20)
        stories_data = summary["stories"]
        
        if not stories_data["available"]:
            print(f"❌ Status check failed: {stories_data.get('error', 'Unknown error')}")
        
        story_counts = stories_data["counts"]
        print(f"Total Stories:     {stories_data['total']}")
        print(f"Todo:              {story_counts['todo']}")
        print(f"In Progress:       {story_counts['in_progress']}")
        print(f"Done:              {story_counts['done']}")
        print(f"Cancelled:         {story_counts['cancelled']}")
        print(f"Total Points:      {stories_data['total_points']}")
        
        # Task Statistics
        print("\n✅ Tasks")
        print("-" * 20)
        tasks_data = summary["tasks"]
        
        if not tasks_data["available"]:
            print(f"❌ Status check failed: {tasks_data.get('error', 'Unknown error')}")
        
        task_counts = tasks_data["counts"]
        print(f"Total Tasks:       {tasks_data['total']}")
        print(f"Todo:              {task_counts['todo']}")
        print(f"In Progress:       {task_counts['in_progress']}")
        print(f"Done:              {task_counts['done']}")
        print(f"Cancelled:         {task_counts['cancelled']}")
        
        # Epic Statistics
        print("\n🎯 Epics")
        print("-" * 20)
        epics_data = summary["epics"]
        
        if not epics_data["available"]:
            print(f"❌ Status check failed: {epics_data.get('error', 'Unknown error')}")
        
        epic_counts = epics_data["counts"]
        print(f"Total Epics:       {epics_data['total']}")
        print(f"Planning:          {epic_counts['planning']}")
        print(f"In Progress:       {epic_counts['in_progress']}")
        print(f"Completed:         {epic_counts['completed']}")
        print(f"Cancelled:         {epic_counts['cancelled']}")
        
        # Sprint Information
        print("\n🏃 Sprints")
        print("-" * 20)
        sprints_data = summary["sprints"]
        
        if not sprints_data["available"]:
            print(f"❌ Status check failed: {sprints_data.get('error', 'Unknown error')}")
        
        print(f"Total Sprints:     {sprints_data['total']}")
        print(f"Active Sprints:    {sprints_data['active_count']}")
        
        for sprint_info in sprints_data["active_sprints"]:
            if sprint_info["available"]:
                progress = sprint_info["progress"]
                print(f"\nActive Sprint: {sprint_info['name']}")
                print(f"  Progress:        {progress['completion_percentage']:.1f}%")
                print(f"  Stories:         {progress['completed_stories']}/{progress['total_stories']}")
                print(f"  Points:          {progress['completed_points']}/{progress['total_points']}")
            else:
                print(f"\nActive Sprint: {sprint_info['name']}")
                print(f"❌ Status check failed: {sprint_info.get('error', 'Unknown error')}")
        
        # Recent Activity (last 5 items)
        print("\n📅 Recent Activity")
        print("-" * 20)
        
        activity_data = summary["recent_activity"]
        if not activity_data["available"]:
            print(f"❌ Activity check failed: {activity_data.get('error', 'Unknown error')}")
        
        recent_items = activity_data["items"]
        if recent_items:
            for item in recent_items:
                item_type = item["type"]
                title = item["title"][:40]
                updated_at = item["updated_at"].strftime('%Y-%m-%d %H:%M')
                print(f"{item_type:8} {title:40} {updated_at}")
        else:
            print("No recent activity found.")
        
        # Health Status
        health_status = summary["health_status"]
        if health_status["is_healthy"]:
            print(f"\n✅ Project: {project_path.name} is healthy and ready!")
        else:
            print(f"\n⚠️  Project: {project_path.name} has {health_status['issue_count']} health issues:")
            for issue in health_status["issues"]:
                print(f"   • {issue}")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli() 