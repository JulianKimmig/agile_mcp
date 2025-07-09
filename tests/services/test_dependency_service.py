"""Tests for dependency service."""

import tempfile

import pytest

from agile_mcp.models.dependency import ArtifactType
from agile_mcp.models.story import StoryStatus
from agile_mcp.server import AgileMCPServer


@pytest.fixture
def server_with_artifacts():
    """Create a server with sample artifacts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        server = AgileMCPServer()
        server.set_project_path(temp_dir)

        # Create sample artifacts
        epic = server.epic_service.create_epic("Test Epic", "Epic description")
        sprint = server.sprint_service.create_sprint("Test Sprint", "Test Sprint description", "Sprint goal")
        story = server.story_service.create_story("Test Story", "Story description")
        task = server.task_service.create_task("Test Task", "Task description")

        yield server, epic, sprint, story, task


def test_add_dependency(server_with_artifacts):
    """Test adding dependencies between artifacts."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Add task depends on story
    success = dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)
    assert success is True

    # Verify dependency was added
    task_updated = server.task_service.get_task(task.id)
    assert story.id in task_updated.dependencies
    assert task_updated.dependencies[story.id] == "story"


def test_remove_dependency(server_with_artifacts):
    """Test removing dependencies."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Add dependency
    dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)

    # Remove dependency
    success = dep_service.remove_dependency(task.id, ArtifactType.TASK, story.id)
    assert success is True

    # Verify dependency was removed
    task_updated = server.task_service.get_task(task.id)
    assert story.id not in task_updated.dependencies


def test_circular_dependency_detection(server_with_artifacts):
    """Test that circular dependencies are detected."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Create a chain: task -> story -> epic
    dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)
    dep_service.add_dependency(story.id, ArtifactType.STORY, epic.id, ArtifactType.EPIC)

    # Try to create circular dependency: epic -> task
    with pytest.raises(ValueError, match="circular dependency"):
        dep_service.add_dependency(epic.id, ArtifactType.EPIC, task.id, ArtifactType.TASK)


def test_get_dependencies(server_with_artifacts):
    """Test getting dependencies for an artifact."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Add multiple dependencies
    dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)
    dep_service.add_dependency(story.id, ArtifactType.STORY, epic.id, ArtifactType.EPIC)

    # Get task dependencies
    task_deps = dep_service.get_dependencies(task.id, ArtifactType.TASK)
    assert len(task_deps) == 1
    assert task_deps[0]["id"] == story.id
    assert task_deps[0]["type"] == "story"
    assert task_deps[0]["name"] == "Test Story"
    assert task_deps[0]["is_completed"] is False


def test_can_start_artifact(server_with_artifacts):
    """Test checking if artifact can be started."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Add dependency: task depends on story
    dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)

    # Task cannot start because story is not done
    result = dep_service.can_start_artifact(task.id, ArtifactType.TASK)
    assert result["can_start"] is False
    assert len(result["blocking_dependencies"]) == 1
    assert result["blocking_dependencies"][0]["id"] == story.id

    # Complete the story
    server.story_service.update_story(story.id, status=StoryStatus.DONE)

    # Now task can start
    result = dep_service.can_start_artifact(task.id, ArtifactType.TASK)
    assert result["can_start"] is True
    assert len(result["blocking_dependencies"]) == 0


def test_cross_artifact_dependencies(server_with_artifacts):
    """Test dependencies between different artifact types."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Sprint depends on epic
    success = dep_service.add_dependency(sprint.id, ArtifactType.SPRINT, epic.id, ArtifactType.EPIC)
    assert success is True

    # Story depends on sprint
    success = dep_service.add_dependency(story.id, ArtifactType.STORY, sprint.id, ArtifactType.SPRINT)
    assert success is True

    # Task depends on story
    success = dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)
    assert success is True

    # Verify all dependencies
    sprint_updated = server.sprint_service.get_sprint(sprint.id)
    assert epic.id in sprint_updated.dependencies

    story_updated = server.story_service.get_story(story.id)
    assert sprint.id in story_updated.dependencies

    task_updated = server.task_service.get_task(task.id)
    assert story.id in task_updated.dependencies


def test_dependency_graph(server_with_artifacts):
    """Test getting the complete dependency graph."""
    server, epic, sprint, story, task = server_with_artifacts
    dep_service = server.dependency_service

    # Create dependencies
    dep_service.add_dependency(sprint.id, ArtifactType.SPRINT, epic.id, ArtifactType.EPIC)
    dep_service.add_dependency(story.id, ArtifactType.STORY, sprint.id, ArtifactType.SPRINT)
    dep_service.add_dependency(task.id, ArtifactType.TASK, story.id, ArtifactType.STORY)

    # Get dependency graph
    graph = dep_service.get_dependency_graph()

    # Verify nodes
    assert len(graph["nodes"]) == 4
    node_ids = [n["id"] for n in graph["nodes"]]
    assert epic.id in node_ids
    assert sprint.id in node_ids
    assert story.id in node_ids
    assert task.id in node_ids

    # Verify edges
    assert len(graph["edges"]) == 3
    edge_pairs = [(e["from"], e["to"]) for e in graph["edges"]]
    assert (epic.id, sprint.id) in edge_pairs
    assert (sprint.id, story.id) in edge_pairs
    assert (story.id, task.id) in edge_pairs
