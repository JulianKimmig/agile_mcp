"""Tests for epic service."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from agile_mcp.services.epic_service import EpicService
from agile_mcp.models.epic import Epic, EpicStatus
from agile_mcp.models.story import UserStory, StoryStatus, Priority


class TestEpicService:
    """Test cases for epic service."""

    @pytest.fixture
    def mock_project_manager(self):
        """Fixture for a mocked project manager."""
        mock_manager = MagicMock()
        mock_manager.is_initialized.return_value = True
        return mock_manager

    @pytest.fixture
    def epic_service(self, mock_project_manager):
        """Fixture for epic service with mocked dependencies."""
        return EpicService(mock_project_manager)

    def test_create_epic_success(self, epic_service, mock_project_manager):
        """Test successful creation of an epic."""
        mock_project_manager.save_epic.return_value = None

        epic = epic_service.create_epic(
            title="Test Epic", 
            description="Test Description"
        )

        assert epic.title == "Test Epic"
        assert epic.description == "Test Description"
        assert epic.status == EpicStatus.PLANNING
        assert epic.story_ids == []
        assert epic.tags == []
        assert epic.id.startswith("EPIC-")
        mock_project_manager.save_epic.assert_called_once_with(epic)

    def test_get_epic_success(self, epic_service, mock_project_manager):
        """Test successful retrieval of an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=[])
        mock_project_manager.get_epic.return_value = mock_epic

        epic = epic_service.get_epic("EPIC-1")

        assert epic == mock_epic
        mock_project_manager.get_epic.assert_called_once_with("EPIC-1")

    def test_get_epic_not_found(self, epic_service, mock_project_manager):
        """Test retrieval of a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        epic = epic_service.get_epic("NON-EXISTENT")

        assert epic is None

    def test_update_epic_success(self, epic_service, mock_project_manager):
        """Test successful update of an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", title="Old Title", description="Old Desc", status=EpicStatus.PLANNING, story_ids=[])
        mock_project_manager.get_epic.return_value = mock_epic
        
        # Create a new mock for the updated epic
        updated_mock = MagicMock(spec=Epic)
        updated_mock.title = "New Title"
        mock_epic.model_copy.return_value = updated_mock
        mock_project_manager.save_epic.return_value = None

        updated_epic = epic_service.update_epic("EPIC-1", title="New Title")

        assert updated_epic.title == "New Title"
        mock_project_manager.save_epic.assert_called_once()

    def test_update_epic_not_found(self, epic_service, mock_project_manager):
        """Test update of a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        updated_epic = epic_service.update_epic("NON-EXISTENT", title="New Title")

        assert updated_epic is None
        mock_project_manager.save_epic.assert_not_called()

    def test_delete_epic_success(self, epic_service, mock_project_manager):
        """Test successful deletion of an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", title="Test Epic", description="Desc", status=EpicStatus.PLANNING, story_ids=["STORY-1"])
        mock_story = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")
        
        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.delete_epic.return_value = True
        mock_project_manager.list_stories.return_value = [mock_story]
        
        # Create updated story mock
        updated_story = MagicMock(spec=UserStory)
        updated_story.epic_id = None
        mock_story.model_copy.return_value = updated_story
        mock_project_manager.save_story.return_value = None

        deleted = epic_service.delete_epic("EPIC-1")

        assert deleted is True
        mock_project_manager.delete_epic.assert_called_once_with("EPIC-1")
        mock_project_manager.save_story.assert_called_once()

    def test_delete_epic_not_found(self, epic_service, mock_project_manager):
        """Test deletion of a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        deleted = epic_service.delete_epic("NON-EXISTENT")

        assert deleted is False
        mock_project_manager.delete_epic.assert_not_called()

    def test_list_epics_success(self, epic_service, mock_project_manager):
        """Test successful listing of epics."""
        # Create real datetime objects for sorting
        mock_epic1 = MagicMock(spec=Epic, id="EPIC-1", status=EpicStatus.PLANNING, story_ids=[])
        mock_epic1.created_at = datetime(2025, 1, 1)
        
        mock_epic2 = MagicMock(spec=Epic, id="EPIC-2", status=EpicStatus.IN_PROGRESS, story_ids=[])
        mock_epic2.created_at = datetime(2025, 1, 2)
        
        # Set up model_copy to return the same objects with modified story_ids
        mock_epic1_copy = MagicMock(spec=Epic)
        mock_epic1_copy.id = "EPIC-1"
        mock_epic1_copy.status = EpicStatus.PLANNING
        mock_epic1_copy.created_at = datetime(2025, 1, 1)
        mock_epic1.model_copy.return_value = mock_epic1_copy
        
        mock_epic2_copy = MagicMock(spec=Epic)
        mock_epic2_copy.id = "EPIC-2"
        mock_epic2_copy.status = EpicStatus.IN_PROGRESS
        mock_epic2_copy.created_at = datetime(2025, 1, 2)
        mock_epic2.model_copy.return_value = mock_epic2_copy
        
        mock_project_manager.list_epics.return_value = [mock_epic1, mock_epic2]

        epics = epic_service.list_epics()

        assert len(epics) == 2
        mock_project_manager.list_epics.assert_called_once()

    def test_list_epics_with_status_filter(self, epic_service, mock_project_manager):
        """Test listing epics with a status filter."""
        # Create real datetime objects for sorting
        mock_epic1 = MagicMock(spec=Epic, id="EPIC-1", status=EpicStatus.PLANNING, story_ids=[])
        mock_epic1.created_at = datetime(2025, 1, 1)
        
        mock_epic2 = MagicMock(spec=Epic, id="EPIC-2", status=EpicStatus.IN_PROGRESS, story_ids=[])
        mock_epic2.created_at = datetime(2025, 1, 2)
        
        # Set up model_copy to return the same objects with modified story_ids
        mock_epic1_copy = MagicMock(spec=Epic)
        mock_epic1_copy.id = "EPIC-1"
        mock_epic1_copy.status = EpicStatus.PLANNING
        mock_epic1_copy.created_at = datetime(2025, 1, 1)
        mock_epic1.model_copy.return_value = mock_epic1_copy
        
        mock_project_manager.list_epics.return_value = [mock_epic1, mock_epic2]

        epics = epic_service.list_epics(status=EpicStatus.PLANNING)

        assert len(epics) == 1
        assert epics[0].status == EpicStatus.PLANNING

    def test_add_story_to_epic_success(self, epic_service, mock_project_manager):
        """Test successfully adding a story to an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=[])
        mock_story = MagicMock(spec=UserStory, id="STORY-1", epic_id=None)
        
        # Set up the update path
        updated_epic = MagicMock(spec=Epic)
        updated_epic.story_ids = ["STORY-1"]
        
        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.get_story.return_value = mock_story
        mock_project_manager.save_epic.return_value = None
        mock_project_manager.save_story.return_value = None

        # Mock the update_epic method call
        epic_service.update_epic = MagicMock(return_value=updated_epic)

        updated_epic_result = epic_service.add_story_to_epic("EPIC-1", "STORY-1")

        assert "STORY-1" in updated_epic_result.story_ids
        epic_service.update_epic.assert_called_once_with("EPIC-1", story_ids=["STORY-1"])

    def test_add_story_to_epic_epic_not_found(self, epic_service, mock_project_manager):
        """Test adding a story to a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        updated_epic = epic_service.add_story_to_epic("NON-EXISTENT", "STORY-1")

        assert updated_epic is None

    def test_remove_story_from_epic_success(self, epic_service, mock_project_manager):
        """Test successfully removing a story from an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=["STORY-1"])
        mock_story = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")
        
        # Set up the update path
        updated_epic = MagicMock(spec=Epic)
        updated_epic.story_ids = []
        
        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.get_story.return_value = mock_story
        mock_project_manager.save_epic.return_value = None
        mock_project_manager.save_story.return_value = None

        # Mock the update_epic method call
        epic_service.update_epic = MagicMock(return_value=updated_epic)

        updated_epic_result = epic_service.remove_story_from_epic("EPIC-1", "STORY-1")

        assert "STORY-1" not in updated_epic_result.story_ids
        epic_service.update_epic.assert_called_once_with("EPIC-1", story_ids=[])

    def test_remove_story_from_epic_epic_not_found(self, epic_service, mock_project_manager):
        """Test removing a story from a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        updated_epic = epic_service.remove_story_from_epic("NON-EXISTENT", "STORY-1")

        assert updated_epic is None

    def test_cleanup_story_references_on_epic_delete(self, epic_service, mock_project_manager):
        """Test that story references are cleaned up when an epic is deleted."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=["STORY-1", "STORY-2"])
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", epic_id="EPIC-1")

        # Set up model_copy returns for stories
        updated_story1 = MagicMock(spec=UserStory)
        updated_story1.epic_id = None
        updated_story2 = MagicMock(spec=UserStory)
        updated_story2.epic_id = None
        
        mock_story1.model_copy.return_value = updated_story1
        mock_story2.model_copy.return_value = updated_story2

        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2]
        mock_project_manager.delete_epic.return_value = True

        epic_service.delete_epic("EPIC-1")

        # Verify that save_story was called with the updated stories
        assert mock_project_manager.save_story.call_count == 2
        assert updated_story1.epic_id is None
        assert updated_story2.epic_id is None
