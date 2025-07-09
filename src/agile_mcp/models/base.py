"""Base model for all agile artifacts."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class AgileArtifact(BaseModel):
    """Base class for all agile artifacts (stories, tasks, sprints, etc.)."""

    id: str = Field(..., description="Unique identifier for the artifact")
    # New unified name field (formerly some models used `title`).
    # A BEFORE-model validator converts incoming data that uses the old `title`
    # field so existing persisted JSON continues to load.
    name: str = Field(..., description="Human-readable name/title of the artifact")
    description: str = Field(..., description="Description of the artifact")
    created_at: datetime = Field(default_factory=datetime.now, description="When the artifact was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the artifact was last updated")
    created_by: Optional[str] = Field(default=None, description="Who created the artifact")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the artifact")
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Dependencies on other artifacts. Key is artifact ID, value is artifact type (epic/sprint/story/task)",
    )

    @property
    def title(self) -> str:
        """Get the title of the artifact."""
        return self.name

    @title.setter
    def title(self, value: str) -> None:
        """Set the title of the artifact."""
        self.name = value

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v}

    # ---------------------------------------------------------------------
    # Compatibility helpers
    # ---------------------------------------------------------------------

    # Use a `model_validator` to map legacy "title" field into the new "name"
    # field before standard validation occurs (Pydantic v2 syntax).
    @model_validator(mode="before")  # type: ignore[misc]
    @classmethod
    def _move_title_to_name(cls, data):  # noqa: D401 (non-imperative verb)
        if isinstance(data, dict) and "name" not in data and "title" in data:
            data = dict(data)
            data["name"] = data["title"]
        if isinstance(data, dict) and "description" not in data:
            data["description"] = f"No description for {data['name']}"
        return data

    # Note: frameworks and downstream code may still use the legacy `title`
    # field on derived models (e.g. `UserStory`, `Task`). Those subclasses
    # declare their own `title` fields, so we intentionally *do not* add an
    # alias property here to avoid interfering with descriptor resolution.
