"""Sprint model."""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import Field, field_validator

from .base import AgileArtifact


class SprintStatus(str, Enum):
    """Status enum for sprints."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sprint(AgileArtifact):
    """Sprint model."""
    
    name: str
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: SprintStatus = SprintStatus.PLANNING
    story_ids: List[str] = Field(default_factory=list, description="List of story IDs in this sprint")
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate that end_date is after start_date if both are provided."""
        if v is not None and hasattr(info, 'data') and 'start_date' in info.data:
            start_date = info.data['start_date']
            if start_date is not None and v <= start_date:
                raise ValueError("End date must be after start date")
        return v
    
    @field_validator('story_ids')
    @classmethod
    def validate_story_ids(cls, v: List[str]) -> List[str]:
        """Validate that all story IDs are strings."""
        if not isinstance(v, list):
            raise ValueError("story_ids must be a list")
        
        for story_id in v:
            if not isinstance(story_id, str):
                raise ValueError("All story IDs must be strings")
        
        return v 