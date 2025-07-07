"""Service layer for sprint management."""

import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import yaml

from ..models.sprint import Sprint, SprintStatus
from ..storage.filesystem import AgileProjectManager


class SprintService:
    """Service for managing sprints with file-based persistence."""
    
    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the sprint service.
        
        Args:
            project_manager: The project manager for file operations
        """
        self.project_manager = project_manager
        self.sprints_dir = project_manager.get_sprints_dir()
    
    def create_sprint(
        self,
        name: str,
        goal: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: SprintStatus = SprintStatus.PLANNING,
        story_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Sprint:
        """Create a new sprint.
        
        Args:
            name: Sprint name
            goal: Sprint goal/objective
            start_date: Sprint start date
            end_date: Sprint end date
            status: Sprint status (default: PLANNING)
            story_ids: List of story IDs assigned to this sprint
            tags: List of tags
            
        Returns:
            The created Sprint
            
        Raises:
            ValueError: If end_date is before start_date
        """
        # Validate dates if both are provided
        if start_date and end_date and end_date <= start_date:
            raise ValueError("End date must be after start date")
        
        # Generate unique ID
        sprint_id = self._generate_sprint_id()
        
        # Create sprint instance
        sprint = Sprint(
            id=sprint_id,
            name=name,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
            status=status,
            story_ids=story_ids or [],
            tags=tags or []
        )
        
        # Persist to file using storage layer
        self.project_manager.save_sprint(sprint)
        
        return sprint
    
    def get_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Retrieve a sprint by ID.
        
        Args:
            sprint_id: The sprint ID to retrieve
            
        Returns:
            The Sprint if found, None otherwise
        """
        return self.project_manager.get_sprint(sprint_id)
    
    def update_sprint(
        self,
        sprint_id: str,
        name: Optional[str] = None,
        goal: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[SprintStatus] = None,
        story_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Sprint]:
        """Update an existing sprint.
        
        Args:
            sprint_id: ID of the sprint to update
            name: New name (optional)
            goal: New goal (optional)
            start_date: New start date (optional)
            end_date: New end date (optional)
            status: New status (optional)
            story_ids: New story IDs (optional)
            tags: New tags (optional)
            
        Returns:
            The updated Sprint if found, None otherwise
            
        Raises:
            ValueError: If end_date is before start_date
        """
        sprint = self.get_sprint(sprint_id)
        if sprint is None:
            return None
        
        # Prepare update data
        update_data = {}
        if name is not None:
            update_data['name'] = name
        if goal is not None:
            update_data['goal'] = goal
        if start_date is not None:
            update_data['start_date'] = start_date
        if end_date is not None:
            update_data['end_date'] = end_date
        if status is not None:
            update_data['status'] = status
        if story_ids is not None:
            update_data['story_ids'] = story_ids
        if tags is not None:
            update_data['tags'] = tags
        
        # Create updated sprint (this will trigger validation)
        updated_sprint = sprint.model_copy(update=update_data)
        
        # Persist changes using storage layer
        self.project_manager.save_sprint(updated_sprint)
        
        return updated_sprint
    
    def delete_sprint(self, sprint_id: str) -> bool:
        """Delete a sprint by ID.
        
        Args:
            sprint_id: ID of the sprint to delete
            
        Returns:
            True if sprint was deleted, False if not found
        """
        return self.project_manager.delete_sprint(sprint_id)
    
    def list_sprints(
        self,
        status: Optional[SprintStatus] = None,
        include_story_ids: bool = False
    ) -> List[Sprint]:
        """List sprints with optional filtering.
        
        Args:
            status: Filter by status (optional)
            include_story_ids: Whether to include story IDs in results
            
        Returns:
            List of Sprint objects matching the filters
        """
        # Get all sprints from storage layer
        sprints = self.project_manager.list_sprints()
        
        # Apply filters
        filtered_sprints = []
        for sprint in sprints:
            if status is not None and sprint.status != status:
                continue
            
            # Optionally exclude story IDs for summary views
            if not include_story_ids:
                sprint = sprint.model_copy(update={"story_ids": []})
            
            filtered_sprints.append(sprint)
        
        sprints = filtered_sprints
        
        # Sort by created date (newest first)
        sprints.sort(key=lambda s: s.created_at, reverse=True)
        
        return sprints
    
    def get_active_sprint(self) -> Optional[Sprint]:
        """Get the currently active sprint.
        
        Returns:
            The active sprint if found, None otherwise
        """
        active_sprints = self.list_sprints(status=SprintStatus.ACTIVE, include_story_ids=True)
        return active_sprints[0] if active_sprints else None
    
    def get_sprints_by_status(self, status: SprintStatus) -> List[Sprint]:
        """Get all sprints with a specific status.
        
        Args:
            status: The sprint status
            
        Returns:
            List of sprints with the specified status
        """
        return self.list_sprints(status=status)
    
    def add_story_to_sprint(self, sprint_id: str, story_id: str) -> Optional[Sprint]:
        """Add a story to a sprint.
        
        Args:
            sprint_id: ID of the sprint
            story_id: ID of the story to add
            
        Returns:
            The updated Sprint if found, None otherwise
        """
        sprint = self.get_sprint(sprint_id)
        if sprint is None:
            return None
        
        # Add story ID if not already present
        story_ids = sprint.story_ids.copy()
        if story_id not in story_ids:
            story_ids.append(story_id)
            
        return self.update_sprint(sprint_id, story_ids=story_ids)
    
    def remove_story_from_sprint(self, sprint_id: str, story_id: str) -> Optional[Sprint]:
        """Remove a story from a sprint.
        
        Args:
            sprint_id: ID of the sprint
            story_id: ID of the story to remove
            
        Returns:
            The updated Sprint if found, None otherwise
        """
        sprint = self.get_sprint(sprint_id)
        if sprint is None:
            return None
        
        # Remove story ID if present
        story_ids = [sid for sid in sprint.story_ids if sid != story_id]
        
        return self.update_sprint(sprint_id, story_ids=story_ids)
    
    def start_sprint(self, sprint_id: str, start_date: Optional[datetime] = None) -> Optional[Sprint]:
        """Start a sprint (change status to ACTIVE).
        
        Args:
            sprint_id: ID of the sprint to start
            start_date: Optional start date (defaults to now)
            
        Returns:
            The updated Sprint if found, None otherwise
        """
        if start_date is None:
            start_date = datetime.now()
            
        return self.update_sprint(
            sprint_id, 
            status=SprintStatus.ACTIVE,
            start_date=start_date
        )
    
    def complete_sprint(self, sprint_id: str, end_date: Optional[datetime] = None) -> Optional[Sprint]:
        """Complete a sprint (change status to COMPLETED).
        
        Args:
            sprint_id: ID of the sprint to complete
            end_date: Optional end date (defaults to now)
            
        Returns:
            The updated Sprint if found, None otherwise
        """
        if end_date is None:
            end_date = datetime.now()
            
        return self.update_sprint(
            sprint_id,
            status=SprintStatus.COMPLETED,
            end_date=end_date
        )
    
    def cancel_sprint(self, sprint_id: str) -> Optional[Sprint]:
        """Cancel a sprint (change status to CANCELLED).
        
        Args:
            sprint_id: ID of the sprint to cancel
            
        Returns:
            The updated Sprint if found, None otherwise
        """
        return self.update_sprint(sprint_id, status=SprintStatus.CANCELLED)
    
    def calculate_sprint_duration(self, sprint_id: str) -> Optional[timedelta]:
        """Calculate the duration of a sprint.
        
        Args:
            sprint_id: ID of the sprint
            
        Returns:
            Duration as timedelta if both dates are set, None otherwise
        """
        sprint = self.get_sprint(sprint_id)
        if not sprint or not sprint.start_date or not sprint.end_date:
            return None
        
        return sprint.end_date - sprint.start_date
    
    def get_sprint_progress(self, sprint_id: str) -> Dict[str, Any]:
        """Get progress information for a sprint.
        
        Args:
            sprint_id: ID of the sprint
            
        Returns:
            Dictionary with progress information
        """
        sprint = self.get_sprint(sprint_id)
        if not sprint:
            return {}
        
        progress = {
            "sprint_id": sprint_id,
            "name": sprint.name,
            "status": sprint.status.value,
            "story_count": len(sprint.story_ids),
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "goal": sprint.goal
        }
        
        # Calculate time-based progress if dates are available
        if sprint.start_date and sprint.end_date:
            now = datetime.now()
            total_duration = sprint.end_date - sprint.start_date
            
            if now < sprint.start_date:
                # Sprint hasn't started yet
                progress["time_progress_percent"] = 0.0
                progress["days_until_start"] = (sprint.start_date - now).days
            elif now > sprint.end_date:
                # Sprint has ended
                progress["time_progress_percent"] = 100.0
                progress["days_overdue"] = (now - sprint.end_date).days
            else:
                # Sprint is active
                elapsed = now - sprint.start_date
                progress["time_progress_percent"] = (elapsed.total_seconds() / total_duration.total_seconds()) * 100
                progress["days_remaining"] = (sprint.end_date - now).days
        
        return progress
    
    def _generate_sprint_id(self) -> str:
        """Generate a unique sprint ID.
        
        Returns:
            A unique sprint ID in format SPRINT-XXXX
        """
        # Generate a 4-character hex string
        hex_part = uuid.uuid4().hex[:4].upper()
        return f"SPRINT-{hex_part}"
    
 