"""User story model."""

from enum import Enum
from typing import Optional

from pydantic import Field

from .base import AgileArtifact


class StoryStatus(str, Enum):
    """Status enum for user stories."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Priority enum for user stories."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class UserStory(AgileArtifact):
    """User story model."""

    status: StoryStatus = StoryStatus.TODO
    priority: Priority = Field(default="medium", description="Story priority")
    points: Optional[int] = Field(default=None, description="Story points (Fibonacci)")
    sprint_id: Optional[str] = Field(default=None, description="ID of the sprint this story is in")

    def is_completed(self) -> bool:
        """Check if story is completed."""
        return self.status == StoryStatus.DONE
