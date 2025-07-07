"""Tests for Sprint model."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from agile_mcp.models.sprint import Sprint, SprintStatus
from agile_mcp.models.base import AgileArtifact


class TestSprintStatus:
    """Test SprintStatus enum."""
    
    def test_sprint_status_values(self):
        """Test that SprintStatus has correct values."""
        assert SprintStatus.PLANNING == "planning"
        assert SprintStatus.ACTIVE == "active"
        assert SprintStatus.COMPLETED == "completed"
        assert SprintStatus.CANCELLED == "cancelled"
    
    def test_sprint_status_from_string(self):
        """Test creating SprintStatus from string."""
        assert SprintStatus("planning") == SprintStatus.PLANNING
        assert SprintStatus("active") == SprintStatus.ACTIVE
        assert SprintStatus("completed") == SprintStatus.COMPLETED
        assert SprintStatus("cancelled") == SprintStatus.CANCELLED


class TestSprint:
    """Test Sprint model."""
    
    def test_sprint_inherits_from_agile_artifact(self):
        """Test that Sprint inherits from AgileArtifact."""
        assert issubclass(Sprint, AgileArtifact)
    
    def test_create_minimal_sprint(self):
        """Test creating a sprint with minimal required fields."""
        sprint = Sprint(
            id="SPRINT-001",
            name="Sprint 1"
        )
        
        assert sprint.id == "SPRINT-001"
        assert sprint.name == "Sprint 1"
        assert sprint.goal is None  # default
        assert sprint.start_date is None  # default
        assert sprint.end_date is None  # default
        assert sprint.status == SprintStatus.PLANNING  # default
        assert sprint.story_ids == []  # default
        
        # Check inherited fields
        assert isinstance(sprint.created_at, datetime)
        assert isinstance(sprint.updated_at, datetime)
        assert sprint.created_by is None
        assert sprint.tags == []
    
    def test_create_complete_sprint(self):
        """Test creating a sprint with all fields."""
        start_date = datetime(2024, 1, 1, 9, 0)
        end_date = datetime(2024, 1, 14, 17, 0)
        
        sprint = Sprint(
            id="SPRINT-002",
            name="Sprint 2 - User Authentication",
            goal="Implement complete user authentication flow",
            start_date=start_date,
            end_date=end_date,
            status=SprintStatus.ACTIVE,
            story_ids=["STORY-001", "STORY-002", "STORY-003"],
            created_by="scrum.master",
            tags=["authentication", "security"]
        )
        
        assert sprint.id == "SPRINT-002"
        assert sprint.name == "Sprint 2 - User Authentication"
        assert sprint.goal == "Implement complete user authentication flow"
        assert sprint.start_date == start_date
        assert sprint.end_date == end_date
        assert sprint.status == SprintStatus.ACTIVE
        assert sprint.story_ids == ["STORY-001", "STORY-002", "STORY-003"]
        assert sprint.created_by == "scrum.master"
        assert sprint.tags == ["authentication", "security"]
    
    def test_id_is_required(self):
        """Test that ID is required."""
        with pytest.raises(ValidationError) as exc_info:
            Sprint(name="Test Sprint")
        
        assert "id" in str(exc_info.value)
    
    def test_name_is_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            Sprint(id="SPRINT-003")
        
        assert "name" in str(exc_info.value)
    
    def test_status_validation(self):
        """Test that status must be valid SprintStatus."""
        # Valid status
        sprint = Sprint(
            id="SPRINT-004",
            name="Test Sprint",
            status=SprintStatus.COMPLETED
        )
        assert sprint.status == SprintStatus.COMPLETED
        
        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            Sprint(
                id="SPRINT-005",
                name="Test Sprint",
                status="invalid_status"
            )
    
    def test_goal_optional(self):
        """Test that goal is optional."""
        sprint = Sprint(
            id="SPRINT-006",
            name="Test Sprint"
        )
        assert sprint.goal is None
        
        sprint_with_goal = Sprint(
            id="SPRINT-007",
            name="Test Sprint",
            goal="Complete user stories for MVP"
        )
        assert sprint_with_goal.goal == "Complete user stories for MVP"
    
    def test_dates_optional(self):
        """Test that start_date and end_date are optional."""
        sprint = Sprint(
            id="SPRINT-008",
            name="Test Sprint"
        )
        assert sprint.start_date is None
        assert sprint.end_date is None
        
        start_date = datetime(2024, 2, 1, 9, 0)
        end_date = datetime(2024, 2, 14, 17, 0)
        
        sprint_with_dates = Sprint(
            id="SPRINT-009",
            name="Test Sprint",
            start_date=start_date,
            end_date=end_date
        )
        assert sprint_with_dates.start_date == start_date
        assert sprint_with_dates.end_date == end_date
    
    def test_date_validation(self):
        """Test date validation - end_date should be after start_date."""
        start_date = datetime(2024, 3, 1, 9, 0)
        end_date = datetime(2024, 3, 14, 17, 0)
        
        # Valid dates (end after start)
        sprint = Sprint(
            id="SPRINT-010",
            name="Test Sprint",
            start_date=start_date,
            end_date=end_date
        )
        assert sprint.start_date == start_date
        assert sprint.end_date == end_date
        
        # Invalid dates (end before start) - should raise ValidationError
        with pytest.raises(ValidationError):
            Sprint(
                id="SPRINT-011",
                name="Test Sprint",
                start_date=end_date,  # Later date
                end_date=start_date   # Earlier date
            )
    
    def test_story_ids_default_empty(self):
        """Test that story_ids defaults to empty list."""
        sprint = Sprint(
            id="SPRINT-012",
            name="Test Sprint"
        )
        assert sprint.story_ids == []
        assert isinstance(sprint.story_ids, list)
    
    def test_story_ids_validation(self):
        """Test story_ids validation."""
        # Empty list is valid
        sprint1 = Sprint(
            id="SPRINT-013",
            name="Test Sprint",
            story_ids=[]
        )
        assert sprint1.story_ids == []
        
        # List with story IDs is valid
        story_ids = ["STORY-001", "STORY-002", "STORY-003"]
        sprint2 = Sprint(
            id="SPRINT-014",
            name="Test Sprint",
            story_ids=story_ids
        )
        assert sprint2.story_ids == story_ids
        
        # Each story ID should be a string
        with pytest.raises(ValidationError):
            Sprint(
                id="SPRINT-015",
                name="Test Sprint",
                story_ids=["STORY-001", 123, "STORY-003"]  # Invalid: number in list
            )
    
    def test_sprint_serialization(self):
        """Test that sprint can be serialized to dict."""
        start_date = datetime(2024, 4, 1, 9, 0)
        end_date = datetime(2024, 4, 14, 17, 0)
        
        sprint = Sprint(
            id="SPRINT-016",
            name="Test Serialization Sprint",
            goal="Test sprint serialization functionality",
            start_date=start_date,
            end_date=end_date,
            status=SprintStatus.ACTIVE,
            story_ids=["STORY-001", "STORY-002"],
            tags=["test", "serialization"]
        )
        
        sprint_dict = sprint.model_dump()
        
        assert sprint_dict["id"] == "SPRINT-016"
        assert sprint_dict["name"] == "Test Serialization Sprint"
        assert sprint_dict["goal"] == "Test sprint serialization functionality"
        assert sprint_dict["status"] == "active"
        assert sprint_dict["story_ids"] == ["STORY-001", "STORY-002"]
        assert sprint_dict["tags"] == ["test", "serialization"]
        assert "start_date" in sprint_dict
        assert "end_date" in sprint_dict
        assert "created_at" in sprint_dict
        assert "updated_at" in sprint_dict
    
    def test_sprint_deserialization(self):
        """Test that sprint can be created from dict."""
        sprint_data = {
            "id": "SPRINT-017",
            "name": "Test Deserialization Sprint",
            "goal": "Test sprint deserialization",
            "status": "completed",
            "story_ids": ["STORY-004", "STORY-005"],
            "tags": ["deserialization"]
        }
        
        sprint = Sprint(**sprint_data)
        
        assert sprint.id == "SPRINT-017"
        assert sprint.name == "Test Deserialization Sprint"
        assert sprint.goal == "Test sprint deserialization"
        assert sprint.status == SprintStatus.COMPLETED
        assert sprint.story_ids == ["STORY-004", "STORY-005"]
        assert sprint.tags == ["deserialization"]
    
    def test_sprint_duration_calculation(self):
        """Test calculating sprint duration."""
        start_date = datetime(2024, 5, 1, 9, 0)
        end_date = datetime(2024, 5, 14, 17, 0)
        
        sprint = Sprint(
            id="SPRINT-018",
            name="Test Duration Sprint",
            start_date=start_date,
            end_date=end_date
        )
        
        # Both dates are set, so we can calculate duration
        assert sprint.start_date is not None
        assert sprint.end_date is not None
        duration = sprint.end_date - sprint.start_date
        assert duration.days == 13  # 14 days minus 1 (same start hour)
    
    def test_sprint_update_timestamp(self):
        """Test that updated_at changes when sprint is modified."""
        sprint = Sprint(
            id="SPRINT-019",
            name="Original Sprint Name"
        )
        original_updated_at = sprint.updated_at
        
        # Simulate some time passing
        import time
        time.sleep(0.01)
        
        # Update the sprint
        updated_sprint = sprint.model_copy(update={"name": "Updated Sprint Name"})
        updated_sprint.updated_at = datetime.now()
        
        assert updated_sprint.updated_at > original_updated_at
        assert updated_sprint.name == "Updated Sprint Name"
        assert updated_sprint.id == sprint.id
    
    def test_sprint_equality(self):
        """Test sprint equality based on ID."""
        sprint1 = Sprint(
            id="SPRINT-020",
            name="Sprint 1"
        )
        
        sprint2 = Sprint(
            id="SPRINT-021",
            name="Sprint 2"
        )
        
        # Different sprints should not be equal
        assert sprint1 != sprint2
        
        # Same sprint with different attributes should be equal (same ID)
        sprint1_copy = sprint1.model_copy(update={"name": "Modified Sprint 1"})
        assert sprint1_copy.id == sprint1.id  # Same ID due to copy
    
    def test_sprint_string_representation(self):
        """Test string representation of sprint."""
        sprint = Sprint(
            id="SPRINT-022",
            name="Sample Sprint",
            goal="Sample sprint for testing"
        )
        
        # Should include key identifying information
        str_repr = str(sprint)
        assert "Sample Sprint" in str_repr
        assert sprint.id in str_repr
    
    def test_sprint_with_story_management(self):
        """Test managing stories in a sprint."""
        sprint = Sprint(
            id="SPRINT-023",
            name="Story Management Sprint",
            story_ids=["STORY-001", "STORY-002"]
        )
        
        # Initial stories
        assert len(sprint.story_ids) == 2
        assert "STORY-001" in sprint.story_ids
        assert "STORY-002" in sprint.story_ids
        
        # Add a story (would be done via service)
        new_story_ids = sprint.story_ids + ["STORY-003"]
        updated_sprint = sprint.model_copy(update={"story_ids": new_story_ids})
        
        assert len(updated_sprint.story_ids) == 3
        assert "STORY-003" in updated_sprint.story_ids
        
        # Remove a story (would be done via service)
        remaining_story_ids = [sid for sid in updated_sprint.story_ids if sid != "STORY-001"]
        final_sprint = updated_sprint.model_copy(update={"story_ids": remaining_story_ids})
        
        assert len(final_sprint.story_ids) == 2
        assert "STORY-001" not in final_sprint.story_ids
        assert "STORY-002" in final_sprint.story_ids
        assert "STORY-003" in final_sprint.story_ids 