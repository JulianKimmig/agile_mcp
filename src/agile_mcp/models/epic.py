"""Epic model."""

from enum import Enum
from typing import List
from pydantic import Field
from datetime import datetime

from .base import AgileArtifact


class EpicStatus(str, Enum):
    """Epic status enumeration."""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Epic(AgileArtifact):
    """Epic model representing a large body of work."""

    status: EpicStatus = Field(default=EpicStatus.PLANNING, description="Epic status")
    story_ids: List[str] = Field(default_factory=list, description="List of story IDs in this epic")

    def add_story(self, story_id: str) -> None:
        """Add a story to the epic.

        If the provided ``story_id`` is not already present in ``story_ids`` it will
        be appended and ``updated_at`` will be refreshed. Duplicate additions are
        ignored to keep the list unique.
        """
        if story_id not in self.story_ids:
            self.story_ids.append(story_id)
            self.updated_at = datetime.now()

    def remove_story(self, story_id: str) -> None:
        """Remove a story from the epic, if it exists.

        This is the logical counterpart to :py:meth:`add_story`. If the
        ``story_id`` is present it will be removed and ``updated_at`` refreshed.
        """
        if story_id in self.story_ids:
            self.story_ids.remove(story_id)
            self.updated_at = datetime.now()
