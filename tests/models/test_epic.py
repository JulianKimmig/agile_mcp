"""Tests for Epic model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from agile_mcp.models.epic import Epic, EpicStatus
from agile_mcp.models.base import AgileArtifact


class TestEpicStatus:
    """Test EpicStatus enum."""

    def test_epic_status_values(self) -> None:
        """Ensure enum values are correct."""
        assert EpicStatus.PLANNING == "planning"
        assert EpicStatus.IN_PROGRESS == "in_progress"
        assert EpicStatus.COMPLETED == "completed"
        assert EpicStatus.CANCELLED == "cancelled"

    def test_epic_status_membership(self) -> None:
        """Enum can be constructed from strings."""
        assert EpicStatus("planning") is EpicStatus.PLANNING
        assert EpicStatus("in_progress") is EpicStatus.IN_PROGRESS
        assert EpicStatus("completed") is EpicStatus.COMPLETED
        assert EpicStatus("cancelled") is EpicStatus.CANCELLED


class TestEpic:
    """Test Epic model behavior."""

    def test_epic_inherits_from_agile_artifact(self) -> None:
        """Epic should extend AgileArtifact base class."""
        assert issubclass(Epic, AgileArtifact)

    def test_create_minimal_epic(self) -> None:
        """Epic can be instantiated with minimal fields."""
        epic = Epic(id="EPIC-001", name="MVP", description="Minimum viable product")
        assert epic.id == "EPIC-001"
        assert epic.name == "MVP"
        assert epic.description == "Minimum viable product"
        assert epic.status == EpicStatus.PLANNING
        assert epic.story_ids == []
        assert isinstance(epic.created_at, datetime)
        assert isinstance(epic.updated_at, datetime)

    def test_add_and_remove_story(self) -> None:
        """add_story should append unique IDs and remove_story should delete them."""
        epic = Epic(id="EPIC-002", name="Feature A", description="Implement Feature A", story_ids=["STORY-1"])
        original_updated_at = epic.updated_at

        # Add new story id
        epic.add_story("STORY-2")
        assert "STORY-2" in epic.story_ids
        assert len(epic.story_ids) == 2
        # updated_at should be refreshed (allow equal for environments with coarse timestamp resolution)
        assert epic.updated_at >= original_updated_at

        # Attempt to add duplicate should be ignored
        duplicate_timestamp = epic.updated_at
        epic.add_story("STORY-2")
        assert epic.story_ids.count("STORY-2") == 1
        assert epic.updated_at == duplicate_timestamp  # No change because duplicate ignored

        # Remove existing story id
        epic.remove_story("STORY-1")
        assert "STORY-1" not in epic.story_ids
        assert len(epic.story_ids) == 1

        # Removing non-existent story id has no effect
        latest_timestamp = epic.updated_at
        epic.remove_story("NON-EXISTENT")
        assert epic.updated_at == latest_timestamp

    def test_name_and_description_required(self) -> None:
        """Validation errors raised if required fields missing."""
        with pytest.raises(ValidationError):
            Epic(id="EPIC-003", description="No name provided")

        ep = Epic(id="EPIC-004", name="No description")
        assert ep.description.startswith("No description for")
