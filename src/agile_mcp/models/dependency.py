"""Cross-artifact dependency model for Agile MCP Server."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """Types of artifacts that can have dependencies."""

    EPIC = "epic"
    SPRINT = "sprint"
    STORY = "story"
    TASK = "task"


class DependencyType(str, Enum):
    """Types of dependencies between artifacts."""

    BLOCKS = "blocks"  # This artifact blocks another
    DEPENDS_ON = "depends_on"  # This artifact depends on another
    RELATES_TO = "relates_to"  # Related but not blocking


class Dependency(BaseModel):
    """Model representing a dependency between two artifacts."""

    artifact_id: str = Field(..., description="ID of the artifact that depends on another")
    artifact_type: ArtifactType = Field(..., description="Type of the dependent artifact")
    depends_on_id: str = Field(..., description="ID of the artifact being depended upon")
    depends_on_type: ArtifactType = Field(..., description="Type of the artifact being depended upon")
    dependency_type: DependencyType = Field(default=DependencyType.DEPENDS_ON, description="Type of dependency")
    description: Optional[str] = Field(default=None, description="Optional description of the dependency")

    def __str__(self) -> str:
        """String representation of the dependency."""
        return f"{self.artifact_type}:{self.artifact_id} {self.dependency_type} {self.depends_on_type}:{self.depends_on_id}"
