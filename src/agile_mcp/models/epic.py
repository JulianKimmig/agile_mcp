"""Epic model."""

from typing import List

from .base import AgileArtifact


class Epic(AgileArtifact):
    """Epic model."""
    
    title: str
    description: str
    story_ids: List[str] = [] 