"""Epic model."""

from enum import Enum
from typing import List
from pydantic import Field

from .base import AgileArtifact


class EpicStatus(str, Enum):
    """Epic status enumeration."""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Epic(AgileArtifact):
    """Epic model representing a large feature or business initiative."""
    
    title: str = Field(..., description="Epic title")
    description: str = Field(..., description="Epic description")
    status: EpicStatus = Field(default=EpicStatus.PLANNING, description="Epic status")
    story_ids: List[str] = Field(default_factory=list, description="List of story IDs in this epic")
    tags: List[str] = Field(default_factory=list, description="Epic tags") 