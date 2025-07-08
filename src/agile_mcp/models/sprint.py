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

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start_date(cls, v: Any) -> datetime | None:
        """Validate and parse start_date from datetime or ISO string."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(f"Invalid datetime format: {v}")
        raise ValueError(f"start_date must be a datetime or ISO string, got {type(v)}")

    @field_validator("end_date", mode="before")
    @classmethod
    def validate_end_date_before(cls, v: Any) -> datetime | None:
        """Validate and parse end_date from datetime or ISO string."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(f"Invalid datetime format: {v}")
        raise ValueError(f"end_date must be a datetime or ISO string, got {type(v)}")

    @field_validator("end_date")
    @classmethod
    def validate_end_date_after_start(cls, v: datetime | None, info: Any) -> datetime | None:
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
