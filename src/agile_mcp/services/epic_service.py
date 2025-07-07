"""Service layer for epic management."""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import yaml

from ..models.epic import Epic, EpicStatus
from ..storage.filesystem import AgileProjectManager
from ..utils.id_generator import generate_epic_id


class EpicService:
    """Service for managing epics with file-based persistence."""
    
    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the epic service.
        
        Args:
            project_manager: The project manager for file operations
        """
        self.project_manager = project_manager
        self.epics_dir = project_manager.get_epics_dir()
    
    def create_epic(
        self,
        title: str,
        description: str,
        status: EpicStatus = EpicStatus.PLANNING,
        story_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Epic:
        """Create a new epic.
        
        Args:
            title: Epic title
            description: Epic description
            status: Epic status (default: PLANNING)
            story_ids: List of story IDs assigned to this epic
            tags: List of tags
            
        Returns:
            The created Epic
        """
        # Generate unique ID
        epic_id = generate_epic_id()
        
        # Create epic instance
        epic = Epic(
            id=epic_id,
            title=title,
            description=description,
            status=status,
            story_ids=story_ids or [],
            tags=tags or []
        )
        
        # Persist to file using storage layer
        self.project_manager.save_epic(epic)
        
        return epic
    
    def get_epic(self, epic_id: str) -> Optional[Epic]:
        """Retrieve an epic by ID.
        
        Args:
            epic_id: The epic ID to retrieve
            
        Returns:
            The Epic if found, None otherwise
        """
        epic = self.project_manager.get_epic(epic_id)
        if epic:
            # Validate and clean broken story references
            epic = self._validate_story_references(epic)
        return epic
    
    def update_epic(
        self,
        epic_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[EpicStatus] = None,
        story_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Epic]:
        """Update an existing epic.
        
        Args:
            epic_id: ID of the epic to update
            title: New title (optional)
            description: New description (optional)
            status: New status (optional)
            story_ids: New story IDs (optional)
            tags: New tags (optional)
            
        Returns:
            The updated Epic if found, None otherwise
        """
        epic = self.get_epic(epic_id)
        if epic is None:
            return None
        
        # Prepare update data
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if status is not None:
            update_data['status'] = status
        if story_ids is not None:
            update_data['story_ids'] = story_ids
        if tags is not None:
            update_data['tags'] = tags
        
        # Create updated epic
        updated_epic = epic.model_copy(update=update_data)
        updated_epic.updated_at = datetime.now()
        
        # Persist changes using storage layer
        self.project_manager.save_epic(updated_epic)
        
        return updated_epic
    
    def delete_epic(self, epic_id: str) -> bool:
        """Delete an epic by ID and clean up references.
        
        Args:
            epic_id: ID of the epic to delete
            
        Returns:
            True if epic was deleted, False if not found
        """
        # Check if epic exists first
        epic = self.get_epic(epic_id)
        if not epic:
            return False
        
        # Remove epic reference from any stories that contain it
        self._cleanup_story_references(epic_id)
        
        # Delete the epic
        deleted = self.project_manager.delete_epic(epic_id)
        
        if deleted:
            print(f"Info: Epic {epic_id} deleted and removed from all story references", file=sys.stderr)
        
        return deleted
    
    def list_epics(
        self,
        status: Optional[EpicStatus] = None,
        include_story_ids: bool = False
    ) -> List[Epic]:
        """List epics with optional filtering.
        
        Args:
            status: Filter by status (optional)
            include_story_ids: Whether to include story IDs in results
            
        Returns:
            List of Epic objects matching the filters
        """
        # Get all epics from storage layer
        epics = self.project_manager.list_epics()
        
        # Apply filters
        filtered_epics = []
        for epic in epics:
            if status is not None and epic.status != status:
                continue
            
            # Validate story references and optionally exclude for summary views
            epic = self._validate_story_references(epic)
            if not include_story_ids:
                epic = epic.model_copy(update={"story_ids": []})
            
            filtered_epics.append(epic)
        
        # Sort by created date (newest first)
        filtered_epics.sort(key=lambda e: e.created_at, reverse=True)
        
        return filtered_epics
    
    def add_story_to_epic(self, epic_id: str, story_id: str) -> Optional[Epic]:
        """Add a story to an epic.
        
        Args:
            epic_id: ID of the epic
            story_id: ID of the story to add
            
        Returns:
            The updated Epic if found, None otherwise
        """
        epic = self.get_epic(epic_id)
        if epic is None:
            return None
        
        # Add story ID if not already present
        story_ids = epic.story_ids.copy()
        if story_id not in story_ids:
            story_ids.append(story_id)
            
        return self.update_epic(epic_id, story_ids=story_ids)
    
    def remove_story_from_epic(self, epic_id: str, story_id: str) -> Optional[Epic]:
        """Remove a story from an epic.
        
        Args:
            epic_id: ID of the epic
            story_id: ID of the story to remove
            
        Returns:
            The updated Epic if found, None otherwise
        """
        epic = self.get_epic(epic_id)
        if epic is None:
            return None
        
        # Remove story ID if present
        story_ids = [sid for sid in epic.story_ids if sid != story_id]
        
        return self.update_epic(epic_id, story_ids=story_ids)
    
    def get_epic_progress(self, epic_id: str) -> Dict[str, Any]:
        """Get progress information for an epic.
        
        Args:
            epic_id: ID of the epic
            
        Returns:
            Dictionary with progress information
        """
        epic = self.get_epic(epic_id)
        if not epic:
            return {}
        
        progress = {
            "epic_id": epic_id,
            "title": epic.title,
            "status": epic.status.value,
            "story_count": len(epic.story_ids),
            "description": epic.description,
            "tags": epic.tags
        }
        
        # Calculate story completion progress
        if epic.story_ids:
            completed_stories = 0
            total_points = 0
            completed_points = 0
            
            for story_id in epic.story_ids:
                story = self.project_manager.get_story(story_id)
                if story:
                    if story.points:
                        total_points += story.points
                        if story.status.value == "done":
                            completed_points += story.points
                    
                    if story.status.value == "done":
                        completed_stories += 1
            
            progress["completed_stories"] = completed_stories
            progress["story_completion_percent"] = (completed_stories / len(epic.story_ids)) * 100 if epic.story_ids else 0
            progress["total_points"] = total_points
            progress["completed_points"] = completed_points
            progress["points_completion_percent"] = (completed_points / total_points) * 100 if total_points > 0 else 0
        else:
            progress["completed_stories"] = 0
            progress["story_completion_percent"] = 0
            progress["total_points"] = 0
            progress["completed_points"] = 0
            progress["points_completion_percent"] = 0
        
        return progress
    

    
    def _validate_story_references(self, epic: Epic) -> Epic:
        """Validate story references and remove broken ones.
        
        Args:
            epic: Epic to validate
            
        Returns:
            Epic with cleaned story references
        """
        if not epic.story_ids:
            return epic
        
        # Use centralized story reference cleaning
        valid_story_ids = self.project_manager.clean_story_references(
            epic.story_ids, "Epic", epic.id
        )
        
        # If references were cleaned, update and save the epic
        if len(valid_story_ids) != len(epic.story_ids):
            # Create updated epic with cleaned references
            updated_epic = epic.model_copy(update={"story_ids": valid_story_ids})
            updated_epic.updated_at = datetime.now()
            
            # Save the cleaned epic
            self.project_manager.save_epic(updated_epic)
            
            return updated_epic
        
        return epic
    
    def _cleanup_story_references(self, epic_id: str) -> None:
        """Remove epic reference from all stories that contain it.
        
        Args:
            epic_id: ID of the epic to remove from stories
        """
        # Get all stories to check for epic references
        stories = self.project_manager.list_stories()
        
        for story in stories:
            if hasattr(story, 'epic_id') and story.epic_id == epic_id:
                # Remove epic reference from story
                updated_story = story.model_copy(update={"epic_id": None})
                updated_story.updated_at = datetime.now()
                
                # Save updated story
                self.project_manager.save_story(updated_story)
                
                print(f"Info: Removed epic reference from story {story.id}", file=sys.stderr) 