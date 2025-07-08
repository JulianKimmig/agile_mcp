"""Integration tests for story deletion cascading cleanup functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path

from agile_mcp.storage.filesystem import AgileProjectManager
from agile_mcp.services.story_service import StoryService
from agile_mcp.services.sprint_service import SprintService
from agile_mcp.services.epic_service import EpicService
from agile_mcp.models.story import Priority
from agile_mcp.models.sprint import SprintStatus
from agile_mcp.models.epic import EpicStatus


class TestStoryCascadingCleanup:
    """Integration tests for story deletion cascading cleanup."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def project_manager(self, temp_project_dir):
        """Create a project manager with initialized project structure."""
        manager = AgileProjectManager(temp_project_dir)
        manager.initialize()
        return manager

    @pytest.fixture
    def story_service(self, project_manager):
        """Create a story service."""
        return StoryService(project_manager)

    @pytest.fixture
    def sprint_service(self, project_manager):
        """Create a sprint service."""
        return SprintService(project_manager)

    @pytest.fixture
    def epic_service(self, project_manager):
        """Create an epic service."""
        return EpicService(project_manager)

    @pytest.fixture
    def sample_stories(self, story_service):
        """Create sample stories for testing."""
        stories = []

        # Create 3 test stories
        story1 = story_service.create_story(
            title="Story 1", description="First test story", priority=Priority.HIGH, points=5
        )
        stories.append(story1)

        story2 = story_service.create_story(
            title="Story 2", description="Second test story", priority=Priority.MEDIUM, points=3
        )
        stories.append(story2)

        story3 = story_service.create_story(
            title="Story 3", description="Third test story", priority=Priority.LOW, points=8
        )
        stories.append(story3)

        return stories

    @pytest.fixture
    def sample_sprint_with_stories(self, sprint_service, sample_stories):
        """Create a sprint containing test stories."""
        sprint = sprint_service.create_sprint(
            name="Test Sprint", goal="Test sprint with stories", status=SprintStatus.ACTIVE
        )

        # Add all sample stories to the sprint
        for story in sample_stories:
            sprint_service.add_story_to_sprint(sprint.id, story.id)

        return sprint

    @pytest.fixture
    def sample_epic_with_stories(self, epic_service, sample_stories):
        """Create an epic containing test stories."""
        epic = epic_service.create_epic(
            title="Test Epic", description="Test epic with stories", status=EpicStatus.PLANNING
        )

        # Add all sample stories to the epic
        for story in sample_stories:
            epic_service.add_story_to_epic(epic.id, story.id)

        return epic

    def test_delete_story_removes_from_sprint(
        self, story_service, sprint_service, sample_stories, sample_sprint_with_stories
    ):
        """Test that deleting a story removes it from sprints."""
        sprint = sample_sprint_with_stories
        story_to_delete = sample_stories[1]  # Middle story

        # Verify story is initially in sprint
        sprint_before = sprint_service.get_sprint(sprint.id)
        assert story_to_delete.id in sprint_before.story_ids
        assert len(sprint_before.story_ids) == 3

        # Delete the story
        result = story_service.delete_story(story_to_delete.id)
        assert result is True

        # Verify story is removed from sprint
        sprint_after = sprint_service.get_sprint(sprint.id)
        assert story_to_delete.id not in sprint_after.story_ids
        assert len(sprint_after.story_ids) == 2

        # Verify other stories are still in sprint
        remaining_story_ids = [sample_stories[0].id, sample_stories[2].id]
        for story_id in remaining_story_ids:
            assert story_id in sprint_after.story_ids

        # Verify deleted story no longer exists
        deleted_story = story_service.get_story(story_to_delete.id)
        assert deleted_story is None

    def test_delete_story_removes_from_epic(
        self, story_service, epic_service, sample_stories, sample_epic_with_stories
    ):
        """Test that deleting a story removes it from epics."""
        epic = sample_epic_with_stories
        story_to_delete = sample_stories[0]  # First story

        # Verify story is initially in epic
        epic_before = epic_service.get_epic(epic.id)
        assert story_to_delete.id in epic_before.story_ids
        assert len(epic_before.story_ids) == 3

        # Delete the story
        result = story_service.delete_story(story_to_delete.id)
        assert result is True

        # Verify story is removed from epic
        epic_after = epic_service.get_epic(epic.id)
        assert story_to_delete.id not in epic_after.story_ids
        assert len(epic_after.story_ids) == 2

        # Verify other stories are still in epic
        remaining_story_ids = [sample_stories[1].id, sample_stories[2].id]
        for story_id in remaining_story_ids:
            assert story_id in epic_after.story_ids

        # Verify deleted story no longer exists
        deleted_story = story_service.get_story(story_to_delete.id)
        assert deleted_story is None

    def test_delete_story_removes_from_both_sprint_and_epic(
        self,
        story_service,
        sprint_service,
        epic_service,
        sample_stories,
        sample_sprint_with_stories,
        sample_epic_with_stories,
    ):
        """Test that deleting a story removes it from both sprints and epics."""
        sprint = sample_sprint_with_stories
        epic = sample_epic_with_stories
        story_to_delete = sample_stories[2]  # Last story

        # Verify story is initially in both sprint and epic
        sprint_before = sprint_service.get_sprint(sprint.id)
        epic_before = epic_service.get_epic(epic.id)
        assert story_to_delete.id in sprint_before.story_ids
        assert story_to_delete.id in epic_before.story_ids

        # Delete the story
        result = story_service.delete_story(story_to_delete.id)
        assert result is True

        # Verify story is removed from both sprint and epic
        sprint_after = sprint_service.get_sprint(sprint.id)
        epic_after = epic_service.get_epic(epic.id)

        assert story_to_delete.id not in sprint_after.story_ids
        assert story_to_delete.id not in epic_after.story_ids

        assert len(sprint_after.story_ids) == 2
        assert len(epic_after.story_ids) == 2

        # Verify other stories are still in both
        remaining_story_ids = [sample_stories[0].id, sample_stories[1].id]
        for story_id in remaining_story_ids:
            assert story_id in sprint_after.story_ids
            assert story_id in epic_after.story_ids

    def test_delete_story_from_multiple_sprints(self, story_service, sprint_service, sample_stories):
        """Test that deleting a story removes it from multiple sprints."""
        # Create multiple sprints
        sprint1 = sprint_service.create_sprint(name="Sprint 1", status=SprintStatus.ACTIVE)
        sprint2 = sprint_service.create_sprint(name="Sprint 2", status=SprintStatus.PLANNING)
        sprint3 = sprint_service.create_sprint(name="Sprint 3", status=SprintStatus.COMPLETED)

        story_to_delete = sample_stories[0]

        # Add the same story to multiple sprints
        sprint_service.add_story_to_sprint(sprint1.id, story_to_delete.id)
        sprint_service.add_story_to_sprint(sprint2.id, story_to_delete.id)
        sprint_service.add_story_to_sprint(sprint3.id, story_to_delete.id)

        # Add other stories to some sprints for verification
        sprint_service.add_story_to_sprint(sprint1.id, sample_stories[1].id)
        sprint_service.add_story_to_sprint(sprint2.id, sample_stories[2].id)

        # Verify story is in all sprints
        for sprint_id in [sprint1.id, sprint2.id, sprint3.id]:
            sprint = sprint_service.get_sprint(sprint_id)
            assert story_to_delete.id in sprint.story_ids

        # Delete the story
        result = story_service.delete_story(story_to_delete.id)
        assert result is True

        # Verify story is removed from all sprints
        for sprint_id in [sprint1.id, sprint2.id, sprint3.id]:
            sprint = sprint_service.get_sprint(sprint_id)
            assert story_to_delete.id not in sprint.story_ids

        # Verify other stories remain in their respective sprints
        sprint1_after = sprint_service.get_sprint(sprint1.id)
        sprint2_after = sprint_service.get_sprint(sprint2.id)
        sprint3_after = sprint_service.get_sprint(sprint3.id)

        assert sample_stories[1].id in sprint1_after.story_ids
        assert sample_stories[2].id in sprint2_after.story_ids
        assert len(sprint3_after.story_ids) == 0  # Only had the deleted story

    def test_delete_story_from_multiple_epics(self, story_service, epic_service, sample_stories):
        """Test that deleting a story removes it from multiple epics."""
        # Create multiple epics
        epic1 = epic_service.create_epic(title="Epic 1", description="First epic")
        epic2 = epic_service.create_epic(title="Epic 2", description="Second epic")
        epic3 = epic_service.create_epic(title="Epic 3", description="Third epic")

        story_to_delete = sample_stories[1]

        # Add the same story to multiple epics
        epic_service.add_story_to_epic(epic1.id, story_to_delete.id)
        epic_service.add_story_to_epic(epic2.id, story_to_delete.id)
        epic_service.add_story_to_epic(epic3.id, story_to_delete.id)

        # Add other stories to some epics for verification
        epic_service.add_story_to_epic(epic1.id, sample_stories[0].id)
        epic_service.add_story_to_epic(epic2.id, sample_stories[2].id)

        # Verify story is in all epics
        for epic_id in [epic1.id, epic2.id, epic3.id]:
            epic = epic_service.get_epic(epic_id)
            assert story_to_delete.id in epic.story_ids

        # Delete the story
        result = story_service.delete_story(story_to_delete.id)
        assert result is True

        # Verify story is removed from all epics
        for epic_id in [epic1.id, epic2.id, epic3.id]:
            epic = epic_service.get_epic(epic_id)
            assert story_to_delete.id not in epic.story_ids

        # Verify other stories remain in their respective epics
        epic1_after = epic_service.get_epic(epic1.id)
        epic2_after = epic_service.get_epic(epic2.id)
        epic3_after = epic_service.get_epic(epic3.id)

        assert sample_stories[0].id in epic1_after.story_ids
        assert sample_stories[2].id in epic2_after.story_ids
        assert len(epic3_after.story_ids) == 0  # Only had the deleted story

    def test_delete_nonexistent_story(self, story_service):
        """Test that deleting a non-existent story returns False."""
        result = story_service.delete_story("STORY-NONEXISTENT")
        assert result is False

    def test_delete_story_preserves_other_artifacts(self, story_service, sprint_service, epic_service, sample_stories):
        """Test that deleting a story doesn't affect unrelated artifacts."""
        # Create additional artifacts not containing the story to delete
        unrelated_sprint = sprint_service.create_sprint(name="Unrelated Sprint")
        unrelated_epic = epic_service.create_epic(title="Unrelated Epic", description="No stories")

        story_to_delete = sample_stories[0]

        # Add different stories to the unrelated artifacts
        sprint_service.add_story_to_sprint(unrelated_sprint.id, sample_stories[1].id)
        epic_service.add_story_to_epic(unrelated_epic.id, sample_stories[2].id)

        # Get initial state
        sprint_before = sprint_service.get_sprint(unrelated_sprint.id)
        epic_before = epic_service.get_epic(unrelated_epic.id)

        # Delete the story (which is not in these artifacts)
        result = story_service.delete_story(story_to_delete.id)
        assert result is True

        # Verify unrelated artifacts are unchanged
        sprint_after = sprint_service.get_sprint(unrelated_sprint.id)
        epic_after = epic_service.get_epic(unrelated_epic.id)

        assert sprint_after.story_ids == sprint_before.story_ids
        assert epic_after.story_ids == epic_before.story_ids

        # Verify the other stories still exist
        assert story_service.get_story(sample_stories[1].id) is not None
        assert story_service.get_story(sample_stories[2].id) is not None

    def test_cleanup_methods_robustness(self, story_service, project_manager):
        """Test that cleanup methods handle edge cases gracefully."""
        # Test with empty artifacts
        story = story_service.create_story(title="Test Story", description="Test")

        # Delete with no sprints or epics existing
        result = story_service.delete_story(story.id)
        assert result is True

        # Verify story is deleted
        assert story_service.get_story(story.id) is None

    def test_data_consistency_after_multiple_deletions(
        self,
        story_service,
        sprint_service,
        epic_service,
        sample_stories,
        sample_sprint_with_stories,
        sample_epic_with_stories,
    ):
        """Test data consistency after multiple story deletions."""
        sprint = sample_sprint_with_stories
        epic = sample_epic_with_stories

        # Delete multiple stories in sequence
        for i, story in enumerate(sample_stories):
            # Verify current state
            current_sprint = sprint_service.get_sprint(sprint.id)
            current_epic = epic_service.get_epic(epic.id)

            expected_count = len(sample_stories) - i
            assert len(current_sprint.story_ids) == expected_count
            assert len(current_epic.story_ids) == expected_count

            # Delete story
            result = story_service.delete_story(story.id)
            assert result is True

            # Verify deletion
            assert story_service.get_story(story.id) is None

        # After all deletions, sprint and epic should be empty
        final_sprint = sprint_service.get_sprint(sprint.id)
        final_epic = epic_service.get_epic(epic.id)

        assert len(final_sprint.story_ids) == 0
        assert len(final_epic.story_ids) == 0

        # But sprint and epic should still exist
        assert final_sprint is not None
        assert final_epic is not None
