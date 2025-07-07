"""Tests for Sprint service."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.agile_mcp.storage.filesystem import AgileProjectManager
from src.agile_mcp.services.sprint_service import SprintService
from src.agile_mcp.models.sprint import Sprint, SprintStatus


class TestSprintService:
    """Test cases for SprintService."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def project_manager(self, temp_project_dir):
        """Create a project manager instance."""
        manager = AgileProjectManager(temp_project_dir)
        manager.initialize()
        return manager
    
    @pytest.fixture
    def sprint_service(self, project_manager):
        """Create a sprint service instance."""
        return SprintService(project_manager)
    
    def test_create_sprint_basic(self, sprint_service):
        """Test creating a basic sprint."""
        sprint = sprint_service.create_sprint(
            name="Sprint 1",
            goal="Implement basic features"
        )
        
        assert sprint.id.startswith("SPRINT-")
        assert sprint.name == "Sprint 1"
        assert sprint.goal == "Implement basic features"
        assert sprint.status == SprintStatus.PLANNING
        assert sprint.story_ids == []
        assert sprint.tags == []
        assert sprint.created_at is not None
        assert sprint.updated_at is not None
    
    def test_create_sprint_with_dates(self, sprint_service):
        """Test creating a sprint with start and end dates."""
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 29)
        
        sprint = sprint_service.create_sprint(
            name="Sprint 2",
            goal="Feature development",
            start_date=start_date,
            end_date=end_date
        )
        
        assert sprint.start_date == start_date
        assert sprint.end_date == end_date
    
    def test_create_sprint_with_tags(self, sprint_service):
        """Test creating a sprint with tags."""
        sprint = sprint_service.create_sprint(
            name="Sprint 3",
            tags=["frontend", "authentication"]
        )
        
        assert sprint.tags == ["frontend", "authentication"]
    
    def test_create_sprint_invalid_dates(self, sprint_service):
        """Test creating a sprint with invalid date range."""
        start_date = datetime(2024, 1, 29)
        end_date = datetime(2024, 1, 15)  # End before start
        
        with pytest.raises(ValueError, match="End date must be after start date"):
            sprint_service.create_sprint(
                name="Invalid Sprint",
                start_date=start_date,
                end_date=end_date
            )
    
    def test_get_sprint_exists(self, sprint_service):
        """Test retrieving an existing sprint."""
        original_sprint = sprint_service.create_sprint(name="Test Sprint")
        
        retrieved_sprint = sprint_service.get_sprint(original_sprint.id)
        
        assert retrieved_sprint is not None
        assert retrieved_sprint.id == original_sprint.id
        assert retrieved_sprint.name == original_sprint.name
    
    def test_get_sprint_not_exists(self, sprint_service):
        """Test retrieving a non-existent sprint."""
        result = sprint_service.get_sprint("SPRINT-NONEXISTENT")
        assert result is None
    
    def test_update_sprint_basic_fields(self, sprint_service):
        """Test updating basic sprint fields."""
        sprint = sprint_service.create_sprint(name="Original Sprint")
        
        updated_sprint = sprint_service.update_sprint(
            sprint.id,
            name="Updated Sprint",
            goal="New goal"
        )
        
        assert updated_sprint is not None
        assert updated_sprint.name == "Updated Sprint"
        assert updated_sprint.goal == "New goal"
        assert updated_sprint.id == sprint.id
    
    def test_update_sprint_status(self, sprint_service):
        """Test updating sprint status."""
        sprint = sprint_service.create_sprint(name="Status Test Sprint")
        
        updated_sprint = sprint_service.update_sprint(
            sprint.id,
            status=SprintStatus.ACTIVE
        )
        
        assert updated_sprint is not None
        assert updated_sprint.status == SprintStatus.ACTIVE
    
    def test_update_sprint_dates(self, sprint_service):
        """Test updating sprint dates."""
        sprint = sprint_service.create_sprint(name="Date Test Sprint")
        
        new_start = datetime(2024, 2, 1)
        new_end = datetime(2024, 2, 14)
        
        updated_sprint = sprint_service.update_sprint(
            sprint.id,
            start_date=new_start,
            end_date=new_end
        )
        
        assert updated_sprint is not None
        assert updated_sprint.start_date == new_start
        assert updated_sprint.end_date == new_end
    
    def test_update_sprint_tags(self, sprint_service):
        """Test updating sprint tags."""
        sprint = sprint_service.create_sprint(name="Tag Test Sprint")
        
        updated_sprint = sprint_service.update_sprint(
            sprint.id,
            tags=["new_tag", "another_tag"]
        )
        
        assert updated_sprint is not None
        assert updated_sprint.tags == ["new_tag", "another_tag"]
    
    def test_update_sprint_not_exists(self, sprint_service):
        """Test updating a non-existent sprint."""
        result = sprint_service.update_sprint("SPRINT-NONEXISTENT", name="New Name")
        assert result is None
    
    def test_delete_sprint_exists(self, sprint_service):
        """Test deleting an existing sprint."""
        sprint = sprint_service.create_sprint(name="Delete Me")
        
        success = sprint_service.delete_sprint(sprint.id)
        assert success is True
        
        # Verify it's deleted
        result = sprint_service.get_sprint(sprint.id)
        assert result is None
    
    def test_delete_sprint_not_exists(self, sprint_service):
        """Test deleting a non-existent sprint."""
        success = sprint_service.delete_sprint("SPRINT-NONEXISTENT")
        assert success is False
    
    def test_list_sprints_empty(self, sprint_service):
        """Test listing sprints when none exist."""
        sprints = sprint_service.list_sprints()
        assert sprints == []
    
    def test_list_sprints_multiple(self, sprint_service):
        """Test listing multiple sprints."""
        sprint1 = sprint_service.create_sprint(name="Sprint 1")
        sprint2 = sprint_service.create_sprint(name="Sprint 2")
        
        sprints = sprint_service.list_sprints()
        
        assert len(sprints) == 2
        # Should be sorted by created_at (newest first)
        assert sprints[0].name == "Sprint 2"  # More recent
        assert sprints[1].name == "Sprint 1"
    
    def test_list_sprints_filter_by_status(self, sprint_service):
        """Test listing sprints filtered by status."""
        sprint1 = sprint_service.create_sprint(name="Planning Sprint")
        sprint2 = sprint_service.create_sprint(name="Active Sprint")
        
        # Make one sprint active
        sprint_service.update_sprint(sprint2.id, status=SprintStatus.ACTIVE)
        
        planning_sprints = sprint_service.list_sprints(status=SprintStatus.PLANNING)
        active_sprints = sprint_service.list_sprints(status=SprintStatus.ACTIVE)
        
        assert len(planning_sprints) == 1
        assert planning_sprints[0].name == "Planning Sprint"
        
        assert len(active_sprints) == 1
        assert active_sprints[0].name == "Active Sprint"
    
    def test_list_sprints_exclude_story_ids(self, sprint_service):
        """Test listing sprints without story IDs."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        sprint_service.update_sprint(sprint.id, story_ids=["STORY-1", "STORY-2"])
        
        sprints = sprint_service.list_sprints(include_story_ids=False)
        
        assert len(sprints) == 1
        assert sprints[0].story_ids == []  # Should be empty
    
    def test_list_sprints_include_story_ids(self, sprint_service):
        """Test listing sprints with story IDs."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        sprint_service.update_sprint(sprint.id, story_ids=["STORY-1", "STORY-2"])
        
        sprints = sprint_service.list_sprints(include_story_ids=True)
        
        assert len(sprints) == 1
        assert sprints[0].story_ids == ["STORY-1", "STORY-2"]
    
    def test_get_active_sprint_none(self, sprint_service):
        """Test getting active sprint when none exists."""
        result = sprint_service.get_active_sprint()
        assert result is None
    
    def test_get_active_sprint_exists(self, sprint_service):
        """Test getting active sprint when one exists."""
        sprint1 = sprint_service.create_sprint(name="Planning Sprint")
        sprint2 = sprint_service.create_sprint(name="Active Sprint")
        
        # Make sprint2 active
        sprint_service.update_sprint(sprint2.id, status=SprintStatus.ACTIVE)
        
        active_sprint = sprint_service.get_active_sprint()
        
        assert active_sprint is not None
        assert active_sprint.id == sprint2.id
        assert active_sprint.status == SprintStatus.ACTIVE
    
    def test_get_sprints_by_status(self, sprint_service):
        """Test getting sprints by specific status."""
        sprint1 = sprint_service.create_sprint(name="Completed Sprint")
        sprint2 = sprint_service.create_sprint(name="Planning Sprint")
        
        # Make sprint1 completed
        sprint_service.update_sprint(sprint1.id, status=SprintStatus.COMPLETED)
        
        completed_sprints = sprint_service.get_sprints_by_status(SprintStatus.COMPLETED)
        planning_sprints = sprint_service.get_sprints_by_status(SprintStatus.PLANNING)
        
        assert len(completed_sprints) == 1
        assert completed_sprints[0].name == "Completed Sprint"
        
        assert len(planning_sprints) == 1
        assert planning_sprints[0].name == "Planning Sprint"
    
    def test_add_story_to_sprint(self, sprint_service):
        """Test adding a story to a sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        updated_sprint = sprint_service.add_story_to_sprint(sprint.id, "STORY-123")
        
        assert updated_sprint is not None
        assert "STORY-123" in updated_sprint.story_ids
    
    def test_add_story_to_sprint_duplicate(self, sprint_service):
        """Test adding the same story twice to a sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        # Add story first time
        sprint_service.add_story_to_sprint(sprint.id, "STORY-123")
        
        # Add same story again
        updated_sprint = sprint_service.add_story_to_sprint(sprint.id, "STORY-123")
        
        assert updated_sprint is not None
        assert updated_sprint.story_ids.count("STORY-123") == 1  # Should only appear once
    
    def test_add_story_to_nonexistent_sprint(self, sprint_service):
        """Test adding a story to a non-existent sprint."""
        result = sprint_service.add_story_to_sprint("SPRINT-NONEXISTENT", "STORY-123")
        assert result is None
    
    def test_remove_story_from_sprint(self, sprint_service):
        """Test removing a story from a sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        # Create actual stories instead of using fake IDs
        from agile_mcp.services.story_service import StoryService
        story_service = StoryService(sprint_service.project_manager)
        story1 = story_service.create_story("Test Story 1", "Description 1")
        story2 = story_service.create_story("Test Story 2", "Description 2")
        
        sprint_service.add_story_to_sprint(sprint.id, story1.id)
        sprint_service.add_story_to_sprint(sprint.id, story2.id)
        
        updated_sprint = sprint_service.remove_story_from_sprint(sprint.id, story1.id)
        
        assert updated_sprint is not None
        assert story1.id not in updated_sprint.story_ids
        assert story2.id in updated_sprint.story_ids
    
    def test_remove_story_not_in_sprint(self, sprint_service):
        """Test removing a story that's not in the sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        updated_sprint = sprint_service.remove_story_from_sprint(sprint.id, "STORY-NOTHERE")
        
        assert updated_sprint is not None
        assert updated_sprint.story_ids == []
    
    def test_remove_story_from_nonexistent_sprint(self, sprint_service):
        """Test removing a story from a non-existent sprint."""
        result = sprint_service.remove_story_from_sprint("SPRINT-NONEXISTENT", "STORY-123")
        assert result is None
    
    def test_start_sprint(self, sprint_service):
        """Test starting a sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        start_time = datetime(2024, 1, 15, 9, 0, 0)
        
        updated_sprint = sprint_service.start_sprint(sprint.id, start_time)
        
        assert updated_sprint is not None
        assert updated_sprint.status == SprintStatus.ACTIVE
        assert updated_sprint.start_date == start_time
    
    def test_start_sprint_no_date(self, sprint_service):
        """Test starting a sprint without specifying start date."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        before_start = datetime.now()
        updated_sprint = sprint_service.start_sprint(sprint.id)
        after_start = datetime.now()
        
        assert updated_sprint is not None
        assert updated_sprint.status == SprintStatus.ACTIVE
        assert before_start <= updated_sprint.start_date <= after_start
    
    def test_complete_sprint(self, sprint_service):
        """Test completing a sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        end_time = datetime(2024, 1, 29, 17, 0, 0)
        
        updated_sprint = sprint_service.complete_sprint(sprint.id, end_time)
        
        assert updated_sprint is not None
        assert updated_sprint.status == SprintStatus.COMPLETED
        assert updated_sprint.end_date == end_time
    
    def test_complete_sprint_no_date(self, sprint_service):
        """Test completing a sprint without specifying end date."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        before_end = datetime.now()
        updated_sprint = sprint_service.complete_sprint(sprint.id)
        after_end = datetime.now()
        
        assert updated_sprint is not None
        assert updated_sprint.status == SprintStatus.COMPLETED
        assert before_end <= updated_sprint.end_date <= after_end
    
    def test_cancel_sprint(self, sprint_service):
        """Test cancelling a sprint."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        updated_sprint = sprint_service.cancel_sprint(sprint.id)
        
        assert updated_sprint is not None
        assert updated_sprint.status == SprintStatus.CANCELLED
    
    def test_calculate_sprint_duration_with_dates(self, sprint_service):
        """Test calculating sprint duration when both dates are set."""
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 29)
        
        sprint = sprint_service.create_sprint(
            name="Test Sprint",
            start_date=start_date,
            end_date=end_date
        )
        
        duration = sprint_service.calculate_sprint_duration(sprint.id)
        
        assert duration is not None
        assert duration == timedelta(days=14)
    
    def test_calculate_sprint_duration_no_dates(self, sprint_service):
        """Test calculating sprint duration when dates are not set."""
        sprint = sprint_service.create_sprint(name="Test Sprint")
        
        duration = sprint_service.calculate_sprint_duration(sprint.id)
        
        assert duration is None
    
    def test_calculate_sprint_duration_nonexistent(self, sprint_service):
        """Test calculating duration for non-existent sprint."""
        duration = sprint_service.calculate_sprint_duration("SPRINT-NONEXISTENT")
        assert duration is None
    
    def test_get_sprint_progress_basic(self, sprint_service):
        """Test getting basic sprint progress."""
        sprint = sprint_service.create_sprint(
            name="Test Sprint",
            goal="Test goal"
        )
        
        # Create actual stories
        from agile_mcp.services.story_service import StoryService
        story_service = StoryService(sprint_service.project_manager)
        story1 = story_service.create_story("Test Story 1", "Description 1")
        story2 = story_service.create_story("Test Story 2", "Description 2")
        
        sprint_service.add_story_to_sprint(sprint.id, story1.id)
        sprint_service.add_story_to_sprint(sprint.id, story2.id)
        
        progress = sprint_service.get_sprint_progress(sprint.id)
        
        assert progress["sprint_id"] == sprint.id
        assert progress["name"] == "Test Sprint"
        assert progress["status"] == "planning"
        assert progress["story_count"] == 2
        assert progress["goal"] == "Test goal"
    
    def test_get_sprint_progress_with_dates(self, sprint_service):
        """Test getting sprint progress with time calculations."""
        # Create a sprint that started yesterday and ends tomorrow
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        sprint = sprint_service.create_sprint(
            name="Active Sprint",
            start_date=start_date,
            end_date=end_date
        )
        
        progress = sprint_service.get_sprint_progress(sprint.id)
        
        assert "time_progress_percent" in progress
        assert "days_remaining" in progress
        assert 0 <= progress["time_progress_percent"] <= 100
        assert progress["days_remaining"] >= 0
    
    def test_get_sprint_progress_future_sprint(self, sprint_service):
        """Test getting progress for a future sprint."""
        start_date = datetime.now() + timedelta(days=1)
        end_date = datetime.now() + timedelta(days=15)
        
        sprint = sprint_service.create_sprint(
            name="Future Sprint",
            start_date=start_date,
            end_date=end_date
        )
        
        progress = sprint_service.get_sprint_progress(sprint.id)
        
        assert progress["time_progress_percent"] == 0.0
        assert "days_until_start" in progress
        assert progress["days_until_start"] >= 0
    
    def test_get_sprint_progress_overdue_sprint(self, sprint_service):
        """Test getting progress for an overdue sprint."""
        start_date = datetime.now() - timedelta(days=15)
        end_date = datetime.now() - timedelta(days=1)
        
        sprint = sprint_service.create_sprint(
            name="Overdue Sprint",
            start_date=start_date,
            end_date=end_date
        )
        
        progress = sprint_service.get_sprint_progress(sprint.id)
        
        assert progress["time_progress_percent"] == 100.0
        assert "days_overdue" in progress
        assert progress["days_overdue"] > 0
    
    def test_get_sprint_progress_nonexistent(self, sprint_service):
        """Test getting progress for non-existent sprint."""
        progress = sprint_service.get_sprint_progress("SPRINT-NONEXISTENT")
        assert progress == {}
    
    def test_generate_sprint_id_unique(self, sprint_service):
        """Test that generated sprint IDs are unique."""
        from agile_mcp.utils.id_generator import generate_sprint_id
        
        ids = set()
        for _ in range(100):
            sprint_id = generate_sprint_id()
            assert sprint_id.startswith("SPRINT-")
            assert len(sprint_id) == 15  # SPRINT- + 8 hex chars
            ids.add(sprint_id)
        
        # With 8 hex chars (4.3 billion possibilities), expect perfect uniqueness
        # in 100 attempts
        assert len(ids) == 100
    
    def test_save_and_load_sprint_persistence(self, sprint_service):
        """Test that sprint data persists correctly."""
        start_date = datetime(2024, 1, 15, 9, 0, 0)
        end_date = datetime(2024, 1, 29, 17, 0, 0)
        
        original_sprint = sprint_service.create_sprint(
            name="Persistence Test",
            goal="Test goal",
            start_date=start_date,
            end_date=end_date,
            status=SprintStatus.ACTIVE,
            tags=["test", "persistence"]
        )
        
        # Create actual stories
        from agile_mcp.services.story_service import StoryService
        story_service = StoryService(sprint_service.project_manager)
        story1 = story_service.create_story("Test Story 1", "Description 1")
        story2 = story_service.create_story("Test Story 2", "Description 2")
        
        # Add some stories
        sprint_service.add_story_to_sprint(original_sprint.id, story1.id)
        sprint_service.add_story_to_sprint(original_sprint.id, story2.id)
        
        # Load the sprint fresh from disk
        loaded_sprint = sprint_service.get_sprint(original_sprint.id)
        
        assert loaded_sprint is not None
        assert loaded_sprint.id == original_sprint.id
        assert loaded_sprint.name == "Persistence Test"
        assert loaded_sprint.goal == "Test goal"
        assert loaded_sprint.start_date == start_date
        assert loaded_sprint.end_date == end_date
        assert loaded_sprint.status == SprintStatus.ACTIVE
        assert loaded_sprint.tags == ["test", "persistence"]
        assert set(loaded_sprint.story_ids) == {story1.id, story2.id} 