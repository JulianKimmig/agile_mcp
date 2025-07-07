"""Service layer for user story management."""

import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml

from ..models.story import UserStory, StoryStatus, Priority
from ..storage.filesystem import AgileProjectManager


class StoryService:
    """Service for managing user stories with file-based persistence."""
    
    # Fibonacci sequence for story points validation
    VALID_FIBONACCI_POINTS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 134 ]
    
    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the story service.
        
        Args:
            project_manager: The project manager for file operations
        """
        self.project_manager = project_manager
        self.stories_dir = project_manager.get_stories_dir()
    
    def create_story(
        self,
        title: str,
        description: str,
        priority: Priority = Priority.MEDIUM,
        status: StoryStatus = StoryStatus.TODO,
        points: Optional[int] = None,
        sprint_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> UserStory:
        """Create a new user story.
        
        Args:
            title: Story title
            description: Story description
            priority: Story priority (default: MEDIUM)
            status: Story status (default: TODO)
            points: Story points (must be Fibonacci number)
            sprint_id: Associated sprint ID
            tags: List of tags
            
        Returns:
            The created UserStory
            
        Raises:
            ValueError: If points is not a valid Fibonacci number
        """
        # Validate story points
        if points is not None:
            points = int(points)
        if points is not None and points not in self.VALID_FIBONACCI_POINTS:
            raise ValueError(f"Story points must be a Fibonacci number: {self.VALID_FIBONACCI_POINTS}")
        
        # Generate unique ID
        story_id = self._generate_story_id()
        
        # Create story instance
        story = UserStory(
            id=story_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            points=points,
            sprint_id=sprint_id,
            tags=tags or []
        )
        
        # Persist to file using storage layer
        self.project_manager.save_story(story)
        
        return story
    
    def get_story(self, story_id: str) -> Optional[UserStory]:
        """Retrieve a story by ID.
        
        Args:
            story_id: The story ID to retrieve
            
        Returns:
            The UserStory if found, None otherwise
        """
        return self.project_manager.get_story(story_id)
    
    def update_story(
        self,
        story_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        status: Optional[StoryStatus] = None,
        points: Optional[int] = None,
        sprint_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[UserStory]:
        """Update an existing story.
        
        Args:
            story_id: ID of the story to update
            title: New title (optional)
            description: New description (optional)
            priority: New priority (optional)
            status: New status (optional)
            points: New points (optional, must be Fibonacci)
            sprint_id: New sprint ID (optional)
            tags: New tags (optional)
            
        Returns:
            The updated UserStory if found, None otherwise
            
        Raises:
            ValueError: If points is not a valid Fibonacci number
        """
        story = self.get_story(story_id)
        if story is None:
            return None
        
        # Validate story points if provided
        if points is not None and points not in self.VALID_FIBONACCI_POINTS:
            raise ValueError(f"Story points must be a Fibonacci number: {self.VALID_FIBONACCI_POINTS}")
        
        # Update fields that were provided
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if priority is not None:
            update_data['priority'] = priority
        if status is not None:
            update_data['status'] = status
        if points is not None:
            update_data['points'] = points
        if sprint_id is not None:
            update_data['sprint_id'] = sprint_id
        if tags is not None:
            update_data['tags'] = tags
        
        # Create updated story
        updated_story = story.model_copy(update=update_data)
        
        # Persist changes using storage layer
        self.project_manager.save_story(updated_story)
        
        return updated_story
    
    def delete_story(self, story_id: str) -> bool:
        """Delete a story by ID.
        
        Args:
            story_id: ID of the story to delete
            
        Returns:
            True if story was deleted, False if not found
        """
        return self.project_manager.delete_story(story_id)
    
    def list_stories(
        self,
        status: Optional[StoryStatus] = None,
        priority: Optional[Priority] = None,
        sprint_id: Optional[str] = None,
        _filter_no_sprint: bool = False
    ) -> List[UserStory]:
        """List stories with optional filtering.
        
        Args:
            status: Filter by status (optional)
            priority: Filter by priority (optional)
            sprint_id: Filter by sprint ID (optional)
            _filter_no_sprint: Internal flag to filter stories with no sprint
            
        Returns:
            List of UserStory objects matching the filters
        """
        # Get all stories from storage layer
        stories = self.project_manager.list_stories()
        
        # Apply filters
        filtered_stories = []
        for story in stories:
            if status is not None and story.status != status:
                continue
            
            if priority is not None and story.priority != priority:
                continue
            
            # Sprint filtering logic
            if sprint_id is not None:
                if story.sprint_id != sprint_id:
                    continue
            elif _filter_no_sprint:
                # Filter for stories with no sprint assignment
                if story.sprint_id is not None:
                    continue
            
            filtered_stories.append(story)
        
        stories = filtered_stories
        
        return stories
    
    def _generate_story_id(self) -> str:
        """Generate a unique story ID.
        
        Returns:
            A unique story ID in format STORY-XXXX
        """
        # Generate a 4-character hex string
        hex_part = uuid.uuid4().hex[:4].upper()
        return f"STORY-{hex_part}"
    
 