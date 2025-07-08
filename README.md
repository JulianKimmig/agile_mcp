# Agile MCP Server

Transform Large Language Models into powerful agile project management assistants through the Model Context Protocol (MCP).

## Overview

The Agile MCP Server provides a comprehensive set of tools for agile project management, including user story creation, sprint planning, progress tracking, and team coordination. It integrates seamlessly with MCP-compatible clients like Claude Desktop and Cursor to bring agile workflows directly into your development environment.

## Why Agile MCP?

- **Empower LLMs**: Turn your LLM into a proactive agile assistant, capable of managing projects, tracking progress, and guiding development workflows.
- **Local & Private**: All your project data is stored locally, ensuring privacy and control.
- **Seamless Integration**: Works with any MCP-compatible client, embedding agile practices directly into your existing development tools.
- **Type-Safe & Robust**: Built with Pydantic for robust data models and type-safe operations, ensuring reliability and maintainability.

## Features

- **User Story Management**: Create, update, and track user stories with priorities, points, and tags
- **Sprint Planning**: Organize stories into time-boxed sprints with goals and timelines
- **Progress Tracking**: Monitor sprint progress, story completion, and team velocity
- **MCP Integration**: Works with any MCP-compatible client for seamless workflow integration
- **Local Storage**: All data stored locally in your project directory
- **Type-Safe**: Full TypeScript support with proper parameter validation

## Quick Start

### Installation

To get started with the Agile MCP Server, clone the repository and install dependencies:

```bash
git clone <repository-url>
cd agile_mcp
uv sync
```

### Running the Server

You can run the server with your project directory:

```bash
uv run python -m agile_mcp --project .
uv run python -m agile_mcp --project .

# Or start without project (set later using tools)
uv run python -m agile_mcp
```

### MCP Client Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "agile-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "agile_mcp", "--project", "/path/to/your/project"],
      "cwd": "/path/to/agile-mcp"
    }
  }
}
```

## Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Comprehensive guide for getting started and daily workflows
- **[API Reference](docs/API_REFERENCE.md)** - Complete documentation of all MCP tools and parameters
- **[Examples](examples/)** - Code examples and usage demonstrations

## Available Tools

### Project Management
- `set_project` - Set the project directory
- `get_project` - Get the current project directory

### User Story Management
- `create_story` - Create a new user story
- `get_story` - Retrieve a story by ID
- `update_story` - Update an existing story
- `list_stories` - List stories with optional filtering
- `delete_story` - Delete a story

### Sprint Management
- `create_sprint` - Create a new sprint
- `get_sprint` - Retrieve a sprint by ID
- `list_sprints` - List sprints with optional filtering
- `update_sprint` - Update an existing sprint
- `manage_sprint_stories` - Add/remove stories from sprints
- `get_sprint_progress` - Get detailed sprint progress
- `get_active_sprint` - Get the currently active sprint

## Project Structure

```
agile_mcp/
├── src/agile_mcp/          # Main source code
│   ├── models/             # Data models (Story, Sprint, etc.)
│   ├── services/           # Business logic services
│   ├── storage/            # File system storage layer
│   ├── tools/              # MCP tool implementations
│   └── server.py           # Main MCP server
├── docs/                   # Documentation
│   ├── API_REFERENCE.md    # Complete API documentation
│   └── USER_GUIDE.md       # User guide and workflows
├── examples/               # Usage examples
├── tests/                  # Test suite
└── README.md               # This file
```

## Development

### Requirements

- Python 3.10+
- uv (for package management)

### Setup Development Environment

```bash
# Install dependencies including dev tools
uv sync

# For development, you can also install the package in editable mode
# This allows you to run examples and tools without full path specifications
uv pip install -e .

# Run tests (includes coverage reporting by default)
uv run pytest

# Run tests with verbose coverage report
uv run pytest -v

# Run tests without coverage (for faster execution)
uv run pytest --no-cov

# Type checking
uv run mypy src/

# Code formatting
uv run ruff format src/ tests/
uv run ruff check src/ tests/
```

### Running Examples

The example scripts demonstrate best practices for using the Agile MCP Server and can be run after setting up the development environment:

```bash
# Option 1: Using uv run (recommended for development)
uv run python examples/basic_usage_demo.py
uv run python examples/sprint_demo.py

# Option 2: After editable installation (alternative)
python examples/basic_usage_demo.py
python examples/sprint_demo.py
```

The examples demonstrate:
- **`basic_usage_demo.py`**: Core functionality including story creation, listing, and updates
- **`sprint_demo.py`**: Complete sprint workflow from creation to completion

Both examples use proper JSON parsing patterns that mirror how real MCP clients handle tool responses, making them excellent references for integration work.

### Test Coverage

The project maintains a minimum test coverage of 75%. Coverage reports are automatically generated when running tests:

- **Terminal Report**: Shows missing lines for each file
- **HTML Report**: Detailed interactive report in `htmlcov/` directory
- **Coverage Threshold**: Tests will fail if coverage drops below 75%

View the HTML coverage report by opening `htmlcov/index.html` in your browser after running tests.

### Transport Options

The server supports multiple transport protocols:

```bash
# STDIO transport (default) - for direct LLM integration
uv run python -m agile_mcp --project . --transport stdio

# SSE transport - for web-based clients
uv run python -m agile_mcp --project . --transport sse --host 0.0.0.0 --port 8000
```

### Project Directory Management

Start the server without a project directory and set it later using the `set_project` tool via your LLM client.

## Examples

### Basic Workflow

```python
# 1. Set up project
set_project(project_path=".")

# 2. Create a user story
create_story(
    title="User Authentication",
    description="Implement secure login system",
    priority="high",
    tags="authentication, security"
)

# 3. Create a sprint
create_sprint(
    name="Sprint 1 - Foundation",
    goal="Establish core functionality",
    start_date="2025-01-07",
    end_date="2025-01-21"
)

# 4. Add story to sprint
manage_sprint_stories(
    sprint_id="SPRINT-123",
    action="add",
    story_id="STORY-456"
)

# 5. Start the sprint
update_sprint(sprint_id="SPRINT-123", status="active")
```

See the [examples directory](examples/) for more detailed usage examples.

## Architecture

The Agile MCP Server follows a clean architecture pattern:

- **Tools Layer**: MCP-compatible tool interfaces
- **Services Layer**: Business logic and workflow management
- **Storage Layer**: File-based persistence with JSON storage
- **Models Layer**: Type-safe data models with Pydantic

All data is stored locally in a `.agile` directory within your project, ensuring full control and privacy of your project data.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Ensure all tests pass (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on the [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) standard
- Inspired by agile development practices and tools
- Uses [FastMCP](https://github.com/jlowin/fastmcp) for MCP server implementation
