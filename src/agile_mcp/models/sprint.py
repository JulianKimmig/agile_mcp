"""Sprint model."""

from datetime import datetime
from enum import Enum
from typing import Any

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
    goal: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: SprintStatus = SprintStatus.PLANNING
    story_ids: list[str] = Field(default_factory=list, description="List of story IDs in this sprint")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime | None, info: Any) -> datetime | None:
        """Validate that end_date is after start_date if both are provided."""
        if v and hasattr(info, "data") and "start_date" in info.data:
            start_date = info.data["start_date"]
            if start_date and v <= start_date:
                raise ValueError("End date must be after start date")
        return v

    @field_validator("story_ids")
    @classmethod
    def validate_story_ids(cls, v: list[str]) -> list[str]:
        """Validate that all story IDs are strings."""
        if not isinstance(v, list):
            raise ValueError("story_ids must be a list")

        for story_id in v:
            if not isinstance(story_id, str):
                raise ValueError("All story IDs must be strings")

        return v
