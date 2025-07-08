"""User story model."""

from enum import Enum
from typing import Optional

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

    title: str
    description: str
    status: StoryStatus = StoryStatus.TODO
    priority: Priority = Priority.MEDIUM
    points: Optional[int] = None
    sprint_id: Optional[str] = None
