"""Story management tools for Agile MCP Server."""

import json
from typing import Dict, Any, Optional, List

from .base import AgileTool, ToolError
from ..models.story import StoryStatus, Priority


class CreateStoryTool(AgileTool):
    """Create a new user story in the agile project."""
    
    def apply(self, title: str, description: str, priority: str = "medium", points: Optional[int] = None, tags: Optional[str] = None) -> str:
        """Create a new user story.
        
        Args:
            title: Story title (required)
            description: Story description (required)
            priority: Story priority (optional, default: medium)
            points: Story points - must be Fibonacci number (optional)
            tags: Comma-separated tags (optional)
            
        Returns:
            Success message with story details
        """
        # Check if project is initialized
        self._check_project_initialized()
        
        # Validate priority
        try:
            priority_enum = Priority(priority)
        except ValueError:
            valid_priorities = [p.value for p in Priority]
            raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")
        
        # Validate story points if provided
        if points is not None:
            valid_points = [1, 2, 3, 5, 8, 13, 21]
            if points not in valid_points:
                raise ToolError(f"Story points must be a Fibonacci number: {valid_points}")
        
        # Parse tags if provided
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]
        
        # Create the story
        story = self.agent.story_service.create_story(
            title=title,
            description=description,
            priority=priority_enum,
            points=points,
            tags=tags_list
        )
        
        # Format result with story data
        story_data = story.model_dump(mode='json')
        self.last_result_data = story_data
        
        return f"User story '{story.title}' created successfully with ID {story.id}"


class GetStoryTool(AgileTool):
    """Retrieve a user story by its ID."""
    
    def apply(self, story_id: str) -> str:
        """Get a user story by ID.
        
        Args:
            story_id: The ID of the story to retrieve (required)
            
        Returns:
            Success message with story details
        """
        # Check if project is initialized
        self._check_project_initialized()
        
        story = self.agent.story_service.get_story(story_id)
        
        if story is None:
            raise ToolError(f"Story with ID {story_id} not found")
        
        # Format result with story data
        story_data = story.model_dump(mode='json')
        self.last_result_data = story_data
        
        return f"Retrieved story: {story.title} (ID: {story.id})"


class UpdateStoryTool(AgileTool):
    """Update an existing user story."""
    
    def apply(self, story_id: str, title: Optional[str] = None, description: Optional[str] = None, 
              priority: Optional[str] = None, status: Optional[str] = None, 
              points: Optional[int] = None, tags: Optional[str] = None) -> str:
        """Update an existing user story.
        
        Args:
            story_id: The ID of the story to update (required)
            title: New story title (optional)
            description: New story description (optional)
            priority: New priority (optional)
            status: New status (optional)
            points: New story points (optional)
            tags: New comma-separated tags (optional)
            
        Returns:
            Success message with updated story details
        """
        # Check if project is initialized
        self._check_project_initialized()
        
        # Validate priority if provided
        if priority is not None:
            try:
                Priority(priority)
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")
        
        # Validate status if provided
        if status is not None:
            try:
                StoryStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in StoryStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate story points if provided
        if points is not None:
            valid_points = [1, 2, 3, 5, 8, 13, 21]
            if points not in valid_points:
                raise ToolError(f"Story points must be a Fibonacci number: {valid_points}")
        
        # Prepare update parameters
        update_params = {}
        if title is not None:
            update_params["title"] = title
        if description is not None:
            update_params["description"] = description
        if priority is not None:
            update_params["priority"] = Priority(priority)
        if status is not None:
            update_params["status"] = StoryStatus(status)
        if points is not None:
            update_params["points"] = points
        if tags is not None:
            update_params["tags"] = [tag.strip() for tag in tags.split(",")]
        
        # Update the story
        updated_story = self.agent.story_service.update_story(story_id, **update_params)
        
        if updated_story is None:
            raise ToolError(f"Story with ID {story_id} not found")
        
        # Format result with story data
        story_data = updated_story.model_dump(mode='json')
        self.last_result_data = story_data
        
        return f"Story '{updated_story.title}' updated successfully"


class ListStoriesTool(AgileTool):
    """List user stories with optional filtering."""
    
    def apply(self, status: Optional[str] = None, priority: Optional[str] = None, sprint_id: Optional[str] = None) -> Dict[str, Any]:
        """List user stories with optional filtering.
        
        Args:
            status: Filter by status (optional)
            priority: Filter by priority (optional)
            sprint_id: Filter by sprint ID (optional)
            
        Returns:
            Structured data with list of stories
        """
        # Check if project is initialized
        self._check_project_initialized()
        
        # Validate status if provided
        if status is not None:
            try:
                StoryStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in StoryStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate priority if provided
        if priority is not None:
            try:
                Priority(priority)
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")
        
        # Convert string filters to enums
        filters = {}
        if status is not None:
            filters["status"] = StoryStatus(status)
        if priority is not None:
            filters["priority"] = Priority(priority)
        if sprint_id is not None:
            filters["sprint_id"] = sprint_id
        
        # Get filtered stories
        stories = self.agent.story_service.list_stories(**filters)
        
        # Convert stories to dict format
        stories_data = [story.model_dump(mode='json') for story in stories]
        
        # Return structured data
        return {
            "stories": stories_data,
            "count": len(stories),
            "filters": {
                "status": status,
                "priority": priority,
                "sprint_id": sprint_id
            }
        }
    
    def _format_message_from_data(self, data: Dict[str, Any]) -> str:
        """Format human-readable message from story list data.
        
        Args:
            data: Structured story list data
            
        Returns:
            Human-readable message string
        """
        count = data.get("count", 0)
        filters = data.get("filters", {})
        
        if count == 0:
            return "No stories found matching the specified criteria"
        
        # Build filter description
        filter_parts = []
        if filters.get("status"):
            filter_parts.append(f"status '{filters['status']}'")
        if filters.get("priority"):
            filter_parts.append(f"priority '{filters['priority']}'")
        if filters.get("sprint_id"):
            filter_parts.append(f"sprint '{filters['sprint_id']}'")
        
        filter_desc = f" matching {', '.join(filter_parts)}" if filter_parts else ""
        
        # Create story summaries
        story_summary = []
        for story in data.get("stories", []):
            status_str = story.get("status", "unknown")
            points_str = f" ({story.get('points')} pts)" if story.get("points") else ""
            sprint_str = f" [Sprint: {story.get('sprint_id')}]" if story.get("sprint_id") else ""
            story_summary.append(f"- {story.get('id')}: {story.get('title')} ({status_str}){points_str}{sprint_str}")
        
        return f"Found {count} stories{filter_desc}:\n" + "\n".join(story_summary)


class DeleteStoryTool(AgileTool):
    """Delete a user story by its ID."""
    
    def apply(self, story_id: str) -> str:
        """Delete a user story by ID.
        
        Args:
            story_id: The ID of the story to delete (required)
            
        Returns:
            Success message confirming deletion
        """
        # Check if project is initialized
        self._check_project_initialized()
        
        # Check if story exists first
        story = self.agent.story_service.get_story(story_id)
        if story is None:
            raise ToolError(f"Story with ID {story_id} not found")
        
        # Delete the story
        success = self.agent.story_service.delete_story(story_id)
        
        if not success:
            raise ToolError(f"Failed to delete story with ID {story_id}")
        
        return f"Story '{story.title}' with ID {story_id} deleted successfully" 