"""Tests for epic service."""

import pytest
from unittest.mock import MagicMock

from agile_mcp.services.epic_service import EpicService
from agile_mcp.models.epic import Epic, EpicStatus
from agile_mcp.models.story import UserStory, StoryStatus, Priority


class TestEpicService:
    """Test cases for epic service."""

    @pytest.fixture
    def mock_project_manager(self):
        """Fixture for a mocked project manager."""
        pm = MagicMock()
        pm.get_epics_dir.return_value = "/mock/epics"
        pm.get_stories_dir.return_value = "/mock/stories"
        return pm

    @pytest.fixture
    def epic_service(self, mock_project_manager):
        """Fixture for an EpicService instance."""
        return EpicService(mock_project_manager)

    def test_create_epic_success(self, epic_service, mock_project_manager):
        """Test successful creation of an epic."""
        mock_project_manager.save_epic.return_value = None # Mock save_epic to do nothing

        epic = epic_service.create_epic(
            title="New Epic",
            description="Description for new epic"
        )

        assert isinstance(epic, Epic)
        assert epic.title == "New Epic"
        assert epic.description == "Description for new epic"
        assert epic.status == EpicStatus.PLANNING
        assert epic.story_ids == []
        mock_project_manager.save_epic.assert_called_once_with(epic)

    def test_get_epic_success(self, epic_service, mock_project_manager):
        """Test successful retrieval of an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", title="Test Epic", description="Desc", status=EpicStatus.PLANNING, story_ids=[])
        mock_project_manager.get_epic.return_value = mock_epic

        epic = epic_service.get_epic("EPIC-1")

        assert epic == mock_epic
        mock_project_manager.get_epic.assert_called_once_with("EPIC-1")

    def test_get_epic_not_found(self, epic_service, mock_project_manager):
        """Test retrieval of a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        epic = epic_service.get_epic("NON-EXISTENT")

        assert epic is None
        mock_project_manager.get_epic.assert_called_once_with("NON-EXISTENT")

    def test_update_epic_success(self, epic_service, mock_project_manager):
        """Test successful update of an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", title="Old Title", description="Old Desc", status=EpicStatus.PLANNING, story_ids=[])
        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.save_epic.return_value = None

        updated_epic = epic_service.update_epic(
            epic_id="EPIC-1",
            title="New Title",
            status=EpicStatus.IN_PROGRESS
        )

        assert updated_epic.title == "New Title"
        assert updated_epic.status == EpicStatus.IN_PROGRESS
        mock_project_manager.save_epic.assert_called_once_with(updated_epic)

    def test_update_epic_not_found(self, epic_service, mock_project_manager):
        """Test update of a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        updated_epic = epic_service.update_epic("NON-EXISTENT", title="New Title")

        assert updated_epic is None
        mock_project_manager.save_epic.assert_not_called()

    def test_delete_epic_success(self, epic_service, mock_project_manager):
        """Test successful deletion of an epic."""
        mock_project_manager.get_epic.return_value = MagicMock(spec=Epic, id="EPIC-1", title="Test Epic", description="Desc", status=EpicStatus.PLANNING, story_ids=["STORY-1"])
        mock_project_manager.delete_epic.return_value = True
        mock_project_manager.get_story.return_value = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")
        mock_project_manager.save_story.return_value = None

        deleted = epic_service.delete_epic("EPIC-1")

        assert deleted is True
        mock_project_manager.delete_epic.assert_called_once_with("EPIC-1")
        mock_project_manager.get_story.assert_called_once_with("STORY-1")
        mock_project_manager.save_story.assert_called_once()

    def test_delete_epic_not_found(self, epic_service, mock_project_manager):
        """Test deletion of a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        deleted = epic_service.delete_epic("NON-EXISTENT")

        assert deleted is False
        mock_project_manager.delete_epic.assert_not_called()

    def test_list_epics_success(self, epic_service, mock_project_manager):
        """Test successful listing of epics."""
        mock_epic1 = MagicMock(spec=Epic, id="EPIC-1", status=EpicStatus.PLANNING)
        mock_epic2 = MagicMock(spec=Epic, id="EPIC-2", status=EpicStatus.IN_PROGRESS)
        mock_project_manager.list_epics.return_value = [mock_epic1, mock_epic2]

        epics = epic_service.list_epics()

        assert epics == [mock_epic1, mock_epic2]
        mock_project_manager.list_epics.assert_called_once()

    def test_list_epics_with_status_filter(self, epic_service, mock_project_manager):
        """Test listing epics with a status filter."""
        mock_epic1 = MagicMock(spec=Epic, id="EPIC-1", status=EpicStatus.PLANNING)
        mock_epic2 = MagicMock(spec=Epic, id="EPIC-2", status=EpicStatus.IN_PROGRESS)
        mock_project_manager.list_epics.return_value = [mock_epic1, mock_epic2]

        epics = epic_service.list_epics(status=EpicStatus.PLANNING)

        assert epics == [mock_epic1]

    def test_add_story_to_epic_success(self, epic_service, mock_project_manager):
        """Test successfully adding a story to an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=[])
        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.get_story.return_value = MagicMock(spec=UserStory, id="STORY-1", epic_id=None)
        mock_project_manager.save_epic.return_value = None
        mock_project_manager.save_story.return_value = None

        updated_epic = epic_service.add_story_to_epic("EPIC-1", "STORY-1")

        assert "STORY-1" in updated_epic.story_ids
        mock_project_manager.save_epic.assert_called_once()
        mock_project_manager.save_story.assert_called_once()

    def test_add_story_to_epic_epic_not_found(self, epic_service, mock_project_manager):
        """Test adding a story to a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        updated_epic = epic_service.add_story_to_epic("NON-EXISTENT", "STORY-1")

        assert updated_epic is None
        mock_project_manager.save_epic.assert_not_called()

    def test_remove_story_from_epic_success(self, epic_service, mock_project_manager):
        """Test successfully removing a story from an epic."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=["STORY-1"])
        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.get_story.return_value = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")
        mock_project_manager.save_epic.return_value = None
        mock_project_manager.save_story.return_value = None

        updated_epic = epic_service.remove_story_from_epic("EPIC-1", "STORY-1")

        assert "STORY-1" not in updated_epic.story_ids
        mock_project_manager.save_epic.assert_called_once()
        mock_project_manager.save_story.assert_called_once()

    def test_remove_story_from_epic_epic_not_found(self, epic_service, mock_project_manager):
        """Test removing a story from a non-existent epic."""
        mock_project_manager.get_epic.return_value = None

        updated_epic = epic_service.remove_story_from_epic("NON-EXISTENT", "STORY-1")

        assert updated_epic is None
        mock_project_manager.save_epic.assert_not_called()

    def test_get_product_backlog_stories(self, epic_service, mock_project_manager):
        """Test retrieving product backlog stories."""
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", sprint_id=None, status=StoryStatus.TODO, priority=Priority.HIGH)
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", sprint_id="SPRINT-1", status=StoryStatus.TODO, priority=Priority.MEDIUM)
        mock_story3 = MagicMock(spec=UserStory, id="STORY-3", sprint_id=None, status=StoryStatus.DONE, priority=Priority.LOW)
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2, mock_story3]

        backlog_stories = epic_service.get_product_backlog_stories()

        assert backlog_stories == [mock_story1, mock_story3] # Should include done stories if not filtered
        mock_project_manager.list_stories.assert_called_once()

    def test_get_product_backlog_stories_filtered_by_status(self, epic_service, mock_project_manager):
        """Test retrieving product backlog stories filtered by status."""
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", sprint_id=None, status=StoryStatus.TODO, priority=Priority.HIGH)
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", sprint_id=None, status=StoryStatus.DONE, priority=Priority.MEDIUM)
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2]

        backlog_stories = epic_service.get_product_backlog_stories(status=StoryStatus.TODO)

        assert backlog_stories == [mock_story1]

    def test_get_product_backlog_stories_filtered_by_priority(self, epic_service, mock_project_manager):
        """Test retrieving product backlog stories filtered by priority."""
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", sprint_id=None, status=StoryStatus.TODO, priority=Priority.HIGH)
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", sprint_id=None, status=StoryStatus.TODO, priority=Priority.MEDIUM)
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2]

        backlog_stories = epic_service.get_product_backlog_stories(priority=Priority.HIGH)

        assert backlog_stories == [mock_story1]

    def test_get_product_backlog_stories_filtered_by_tags(self, epic_service, mock_project_manager):
        """Test retrieving product backlog stories filtered by tags."""
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", sprint_id=None, status=StoryStatus.TODO, tags=["backend"], priority=Priority.HIGH)
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", sprint_id=None, status=StoryStatus.TODO, tags=["frontend"], priority=Priority.MEDIUM)
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2]

        backlog_stories = epic_service.get_product_backlog_stories(tags=["backend"])

        assert backlog_stories == [mock_story1]

    def test_get_product_backlog_stories_sorted(self, epic_service, mock_project_manager):
        """Test retrieving product backlog stories sorted by priority and creation date."""
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", sprint_id=None, status=StoryStatus.TODO, priority=Priority.HIGH, created_at=datetime(2025, 1, 3))
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", sprint_id=None, status=StoryStatus.TODO, priority=Priority.MEDIUM, created_at=datetime(2025, 1, 1))
        mock_story3 = MagicMock(spec=UserStory, id="STORY-3", sprint_id=None, status=StoryStatus.TODO, priority=Priority.HIGH, created_at=datetime(2025, 1, 2))
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2, mock_story3]

        backlog_stories = epic_service.get_product_backlog_stories()

        assert backlog_stories == [mock_story1, mock_story3, mock_story2] # High, then High (newer), then Medium

    def test_cleanup_story_references_on_epic_delete(self, epic_service, mock_project_manager):
        """Test that story references are cleaned up when an epic is deleted."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=["STORY-1", "STORY-2"])
        mock_story1 = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")
        mock_story2 = MagicMock(spec=UserStory, id="STORY-2", epic_id="EPIC-1")

        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.list_stories.return_value = [mock_story1, mock_story2]
        mock_project_manager.delete_epic.return_value = True

        epic_service.delete_epic("EPIC-1")

        # Verify that epic_id was set to None for the stories
        mock_project_manager.save_story.assert_any_call(mock_story1)
        mock_project_manager.save_story.assert_any_call(mock_story2)
        assert mock_story1.epic_id is None
        assert mock_story2.epic_id is None

    def test_add_story_to_epic_updates_story_epic_id(self, epic_service, mock_project_manager):
        """Test that adding a story to an epic updates the story's epic_id."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=[])
        mock_story = MagicMock(spec=UserStory, id="STORY-1", epic_id=None)

        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.get_story.return_value = mock_story
        mock_project_manager.save_epic.return_value = None
        mock_project_manager.save_story.return_value = None

        epic_service.add_story_to_epic("EPIC-1", "STORY-1")

        assert mock_story.epic_id == "EPIC-1"
        mock_project_manager.save_story.assert_called_once_with(mock_story)

    def test_remove_story_from_epic_clears_story_epic_id(self, epic_service, mock_project_manager):
        """Test that removing a story from an epic clears the story's epic_id."""
        mock_epic = MagicMock(spec=Epic, id="EPIC-1", story_ids=["STORY-1"])
        mock_story = MagicMock(spec=UserStory, id="STORY-1", epic_id="EPIC-1")

        mock_project_manager.get_epic.return_value = mock_epic
        mock_project_manager.get_story.return_value = mock_story
        mock_project_manager.save_epic.return_value = None
        mock_project_manager.save_story.return_value = None

        epic_service.remove_story_from_epic("EPIC-1", "STORY-1")

        assert mock_story.epic_id is None
        mock_project_manager.save_story.assert_called_once_with(mock_story)
