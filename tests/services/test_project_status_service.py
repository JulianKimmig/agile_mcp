"""Tests for ProjectStatusService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from agile_mcp.services.project_status_service import ProjectStatusService


class TestProjectStatusService:
    """Test cases for ProjectStatusService."""

    @pytest.fixture
    def mock_project_manager(self):
        """Create a mock project manager."""
        return Mock()

    @pytest.fixture
    def service(self, mock_project_manager):
        """Create a ProjectStatusService with mocked dependencies."""
        service = ProjectStatusService(mock_project_manager)

        # Mock all the services
        service.config_service = Mock()
        service.story_service = Mock()
        service.sprint_service = Mock()
        service.task_service = Mock()
        service.epic_service = Mock()

        return service

    def test_get_project_summary_structure(self, service):
        """Test that get_project_summary returns the expected structure."""
        # Mock all service methods to return basic data
        service.config_service.get_project_config.return_value = {"name": "Test Project", "version": "1.0.0"}
        service.config_service.get_agile_config.return_value = {"methodology": "Scrum", "sprint_duration_weeks": 2}
        service.story_service.list_stories.return_value = []
        service.task_service.list_tasks.return_value = []
        service.epic_service.list_epics.return_value = []
        service.sprint_service.list_sprints.return_value = []

        summary = service.get_project_summary()

        # Verify all expected keys are present
        expected_keys = [
            "project_config",
            "agile_config",
            "stories",
            "tasks",
            "epics",
            "sprints",
            "recent_activity",
            "health_status",
        ]

        assert all(key in summary for key in expected_keys)

    def test_project_config_success(self, service):
        """Test successful project configuration retrieval."""
        config_data = {"name": "Test Project", "version": "1.0.0"}
        service.config_service.get_project_config.return_value = config_data

        result = service._get_project_config()

        assert result["name"] == "Test Project"
        assert result["version"] == "1.0.0"
        assert result["available"] is True
        assert "error" not in result

    def test_project_config_error(self, service):
        """Test project configuration retrieval with error."""
        service.config_service.get_project_config.side_effect = Exception("Config error")

        result = service._get_project_config()

        assert result["name"] == "N/A"
        assert result["version"] == "N/A"
        assert result["available"] is False
        assert result["error"] == "Config error"

    def test_agile_config_success(self, service):
        """Test successful agile configuration retrieval."""
        config_data = {"methodology": "Scrum", "sprint_duration_weeks": 2, "story_point_scale": "Fibonacci"}
        service.config_service.get_agile_config.return_value = config_data

        result = service._get_agile_config()

        assert result["methodology"] == "Scrum"
        assert result["sprint_duration_weeks"] == 2
        assert result["story_point_scale"] == "Fibonacci"
        assert result["available"] is True

    def test_agile_config_error(self, service):
        """Test agile configuration retrieval with error."""
        service.config_service.get_agile_config.side_effect = Exception("Agile config error")

        result = service._get_agile_config()

        assert result["methodology"] == "N/A"
        assert result["sprint_duration_weeks"] == "N/A"
        assert result["story_point_scale"] == "N/A"
        assert result["available"] is False
        assert result["error"] == "Agile config error"

    def test_story_statistics_with_data(self, service):
        """Test story statistics with actual story data."""
        # Create mock stories with different statuses and points
        stories = [
            Mock(status=Mock(value="todo"), points=5),
            Mock(status=Mock(value="in_progress"), points=3),
            Mock(status=Mock(value="done"), points=8),
            Mock(status=Mock(value="done"), points=None),  # Story without points
            Mock(status=Mock(value="cancelled"), points=2),
        ]
        service.story_service.list_stories.return_value = stories

        result = service._get_story_statistics()

        assert result["total"] == 5
        assert result["counts"]["todo"] == 1
        assert result["counts"]["in_progress"] == 1
        assert result["counts"]["done"] == 2
        assert result["counts"]["cancelled"] == 1
        assert result["total_points"] == 18  # 5 + 3 + 8 + 2
        assert result["available"] is True

    def test_story_statistics_none_return(self, service):
        """Test story statistics when service returns None."""
        service.story_service.list_stories.return_value = None

        result = service._get_story_statistics()

        assert result["total"] == 0
        assert result["counts"]["todo"] == 0
        assert result["total_points"] == 0
        assert result["available"] is True

    def test_story_statistics_error(self, service):
        """Test story statistics with service error."""
        service.story_service.list_stories.side_effect = Exception("Story service error")

        result = service._get_story_statistics()

        assert result["total"] == 0
        assert result["available"] is False
        assert result["error"] == "Story service error"

    def test_task_statistics_with_data(self, service):
        """Test task statistics with actual task data."""
        tasks = [
            Mock(status=Mock(value="todo")),
            Mock(status=Mock(value="in_progress")),
            Mock(status=Mock(value="done")),
            Mock(status=Mock(value="done")),
        ]
        service.task_service.list_tasks.return_value = tasks

        result = service._get_task_statistics()

        assert result["total"] == 4
        assert result["counts"]["todo"] == 1
        assert result["counts"]["in_progress"] == 1
        assert result["counts"]["done"] == 2
        assert result["available"] is True

    def test_task_statistics_error(self, service):
        """Test task statistics with service error."""
        service.task_service.list_tasks.side_effect = Exception("Task service error")

        result = service._get_task_statistics()

        assert result["total"] == 0
        assert result["available"] is False
        assert result["error"] == "Task service error"

    def test_epic_statistics_with_data(self, service):
        """Test epic statistics with actual epic data."""
        epics = [
            Mock(status=Mock(value="planning")),
            Mock(status=Mock(value="in_progress")),
            Mock(status=Mock(value="completed")),
        ]
        service.epic_service.list_epics.return_value = epics

        result = service._get_epic_statistics()

        assert result["total"] == 3
        assert result["counts"]["planning"] == 1
        assert result["counts"]["in_progress"] == 1
        assert result["counts"]["completed"] == 1
        assert result["available"] is True

    def test_epic_statistics_error(self, service):
        """Test epic statistics with service error."""
        service.epic_service.list_epics.side_effect = Exception("Epic service error")

        result = service._get_epic_statistics()

        assert result["total"] == 0
        assert result["available"] is False
        assert result["error"] == "Epic service error"

    def test_sprint_information_with_active_sprints(self, service):
        """Test sprint information with active sprints."""
        # Create properly configured mock sprints
        sprint1 = Mock()
        sprint1.id = "SPRINT-1"
        sprint1.name = "Sprint 1"
        sprint1.status.value = "active"

        sprint2 = Mock()
        sprint2.id = "SPRINT-2"
        sprint2.name = "Sprint 2"
        sprint2.status.value = "completed"

        sprint3 = Mock()
        sprint3.id = "SPRINT-3"
        sprint3.name = "Sprint 3"
        sprint3.status.value = "active"

        sprints = [sprint1, sprint2, sprint3]
        service.sprint_service.list_sprints.return_value = sprints

        # Mock progress data for active sprints
        progress_data = {
            "completion_percentage": 75.0,
            "completed_stories": 3,
            "total_stories": 4,
            "completed_points": 15,
            "total_points": 20,
        }
        service.sprint_service.get_sprint_progress.return_value = progress_data

        result = service._get_sprint_information()

        assert result["total"] == 3
        assert result["active_count"] == 2
        assert len(result["active_sprints"]) == 2
        assert result["active_sprints"][0]["name"] == "Sprint 1"
        assert result["active_sprints"][0]["progress"] == progress_data
        assert result["active_sprints"][0]["available"] is True
        assert result["available"] is True

    def test_sprint_information_progress_error(self, service):
        """Test sprint information when progress retrieval fails."""
        # Create properly configured mock sprint
        sprint1 = Mock()
        sprint1.id = "SPRINT-1"
        sprint1.name = "Sprint 1"
        sprint1.status.value = "active"

        sprints = [sprint1]
        service.sprint_service.list_sprints.return_value = sprints
        service.sprint_service.get_sprint_progress.side_effect = Exception("Progress error")

        result = service._get_sprint_information()

        assert result["total"] == 1
        assert result["active_count"] == 1
        assert len(result["active_sprints"]) == 1
        assert result["active_sprints"][0]["name"] == "Sprint 1"
        assert result["active_sprints"][0]["progress"] is None
        assert result["active_sprints"][0]["available"] is False
        assert result["active_sprints"][0]["error"] == "Progress error"

    def test_sprint_information_error(self, service):
        """Test sprint information with service error."""
        service.sprint_service.list_sprints.side_effect = Exception("Sprint service error")

        result = service._get_sprint_information()

        assert result["total"] == 0
        assert result["active_count"] == 0
        assert result["active_sprints"] == []
        assert result["available"] is False
        assert result["error"] == "Sprint service error"

    def test_recent_activity_with_data(self, service):
        """Test recent activity aggregation with data from all services."""
        # Mock datetime objects
        now = datetime.now(timezone.utc)

        # Mock data from different services
        stories = [Mock(title="Story 1", updated_at=now)]
        tasks = [Mock(title="Task 1", updated_at=now)]
        epics = [Mock(title="Epic 1", updated_at=now)]
        sprints = [Mock(name="Sprint 1", updated_at=now)]

        service.story_service.list_stories.return_value = stories
        service.task_service.list_tasks.return_value = tasks
        service.epic_service.list_epics.return_value = epics
        service.sprint_service.list_sprints.return_value = sprints

        result = service._get_recent_activity()

        assert result["available"] is True
        assert len(result["items"]) == 4

        # Check that all types are represented
        types = [item["type"] for item in result["items"]]
        assert "Story" in types
        assert "Task" in types
        assert "Epic" in types
        assert "Sprint" in types

    def test_recent_activity_with_service_errors(self, service):
        """Test recent activity when some services fail."""
        # Mock one service working, others failing
        service.story_service.list_stories.return_value = [Mock(title="Story 1", updated_at=datetime.now(timezone.utc))]
        service.task_service.list_tasks.side_effect = Exception("Task error")
        service.epic_service.list_epics.side_effect = Exception("Epic error")
        service.sprint_service.list_sprints.side_effect = Exception("Sprint error")

        result = service._get_recent_activity()

        assert result["available"] is True
        assert len(result["items"]) == 1
        assert result["items"][0]["type"] == "Story"

    def test_recent_activity_empty_with_all_service_errors(self, service):
        """Test recent activity when all services fail - should return empty but available."""
        service.story_service.list_stories.side_effect = Exception("Story error")
        service.task_service.list_tasks.side_effect = Exception("Task error")
        service.epic_service.list_epics.side_effect = Exception("Epic error")
        service.sprint_service.list_sprints.side_effect = Exception("Sprint error")

        result = service._get_recent_activity()

        # All individual service errors are swallowed, so it should still be available but empty
        assert result["available"] is True
        assert result["items"] == []

    def test_health_status_healthy(self, service):
        """Test health status when all services are healthy."""
        service.config_service.get_project_config.return_value = {}
        service.story_service.list_stories.return_value = []
        service.task_service.list_tasks.return_value = []

        result = service._get_health_status()

        assert result["is_healthy"] is True
        assert result["issues"] == []
        assert result["issue_count"] == 0

    def test_health_status_with_issues(self, service):
        """Test health status when services have issues."""
        service.config_service.get_project_config.side_effect = Exception("Config error")
        service.story_service.list_stories.return_value = None
        service.task_service.list_tasks.side_effect = Exception("Task error")

        result = service._get_health_status()

        assert result["is_healthy"] is False
        assert len(result["issues"]) == 3
        assert "Project configuration not accessible" in result["issues"]
        assert "Story service returned None" in result["issues"]
        assert "Task service error: Task error" in result["issues"]
        assert result["issue_count"] == 3

    def test_full_integration_success(self, service):
        """Test full integration with all services working."""
        # Create properly configured mock objects with datetime attributes for recent activity
        story_mock = Mock()
        story_mock.status.value = "todo"
        story_mock.points = 5
        story_mock.title = "Test Story"
        story_mock.updated_at = datetime.now(timezone.utc)

        task_mock = Mock()
        task_mock.status.value = "done"
        task_mock.title = "Test Task"
        task_mock.updated_at = datetime.now(timezone.utc)

        epic_mock = Mock()
        epic_mock.status.value = "planning"
        epic_mock.title = "Test Epic"
        epic_mock.updated_at = datetime.now(timezone.utc)

        # Mock all services to return data
        service.config_service.get_project_config.return_value = {"name": "Test", "version": "1.0"}
        service.config_service.get_agile_config.return_value = {"methodology": "Scrum"}
        service.story_service.list_stories.return_value = [story_mock]
        service.task_service.list_tasks.return_value = [task_mock]
        service.epic_service.list_epics.return_value = [epic_mock]
        service.sprint_service.list_sprints.return_value = []

        summary = service.get_project_summary()

        # Verify all sections are available
        assert summary["project_config"]["available"] is True
        assert summary["agile_config"]["available"] is True
        assert summary["stories"]["available"] is True
        assert summary["tasks"]["available"] is True
        assert summary["epics"]["available"] is True
        assert summary["sprints"]["available"] is True
        assert summary["recent_activity"]["available"] is True
        assert summary["health_status"]["is_healthy"] is True

    def test_full_integration_with_errors(self, service):
        """Test full integration with some services failing."""
        # Mock some services to fail
        service.config_service.get_project_config.side_effect = Exception("Config error")
        service.story_service.list_stories.return_value = None
        service.task_service.list_tasks.return_value = []
        service.epic_service.list_epics.side_effect = Exception("Epic error")
        service.sprint_service.list_sprints.return_value = []

        summary = service.get_project_summary()

        # Verify error handling
        assert summary["project_config"]["available"] is False
        assert summary["stories"]["available"] is True  # Handles None gracefully
        assert summary["tasks"]["available"] is True
        assert summary["epics"]["available"] is False
        assert summary["sprints"]["available"] is True
        assert summary["health_status"]["is_healthy"] is False
