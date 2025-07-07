"""Base model for all agile artifacts."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AgileArtifact(BaseModel):
    """Base class for all agile artifacts (stories, tasks, sprints, etc.)."""
    
    id: str = Field(..., description="Unique identifier for the artifact")
    created_at: datetime = Field(default_factory=datetime.now, description="When the artifact was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the artifact was last updated")
    created_by: Optional[str] = Field(default=None, description="Who created the artifact")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the artifact")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 