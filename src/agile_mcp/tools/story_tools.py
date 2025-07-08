"""Story management tools for Agile MCP Server."""

from typing import Any

from ..models.story import Priority, StoryStatus
from .base import AgileTool, ToolError, ToolResult


class CreateStoryTool(AgileTool):
    """Tool to create new user story."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for story creation."""
        pass  # Default implementation - no validation

    def apply(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        points: int | None = None,
        tags: str | None = None,
    ) -> ToolResult:
        """Create a new user story.

        Args:
            title: Story title (required)
            description: Story description (required)
            priority: Story priority. Options: critical, high, medium, low
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
        if points:
            valid_points = [1, 2, 3, 5, 8, 13, 21]
            if points not in valid_points:
                raise ToolError(f"Story points must be a Fibonacci number: {valid_points}")

        # Parse tags if provided
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]

        # Create the story
        try:
            story_data = {
                "title": title,
                "description": description,
                "priority": priority_enum,
                "points": points,
                "tags": tags_list,
            }
            # Check if story service is available
            if self.agent.story_service is None:
                raise ToolError("Story service not available")

            story = self.agent.story_service.create_story(**story_data)
        except Exception as err:
            raise RuntimeError("Failed to create story.") from err

        # Format result with story data
        story_data = story.model_dump(mode="json")

        return self.format_result(f"User story '{story.title}' created successfully with ID {story.id}", story_data)


class GetStoryTool(AgileTool):
    """Tool for retrieving user stories."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for story retrieval."""
        pass  # Default implementation - no validation

    def apply(self, story_id: str) -> ToolResult:
        """Get a user story by ID.

        Args:
            story_id: The ID of the story to retrieve (required)

        Returns:
            Success message with story details
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Check if story service is available
            if self.agent.story_service is None:
                raise ToolError("Story service not available")

            story = self.agent.story_service.get_story(story_id)
        except Exception as err:
            raise RuntimeError("Failed to load story.") from err

        if story is None:
            raise ToolError(f"Story with ID {story_id} not found")

        # Format result with story data
        story_data = story.model_dump(mode="json")

        return self.format_result(f"Retrieved story: {story.title} (ID: {story.id})", story_data)


class UpdateStoryTool(AgileTool):
    """Tool for updating existing user stories."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for story update."""
        pass  # Default implementation - no validation

    def apply(
        self,
        story_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        points: int | None = None,
        tags: str | None = None,
    ) -> ToolResult:
        """Update an existing user story.

        Args:
            story_id: The ID of the story to update (required)
            title: New story title (optional)
            description: New story description (optional)
            priority: New priority. Options: critical, high, medium, low
            status: New status. Options: todo, in_progress, in_review, done, blocked
            points: New story points (optional)
            tags: New comma-separated tags (optional)

        Returns:
            Success message with updated story details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate priority if provided
        if priority:
            try:
                Priority(priority)
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")

        # Validate status if provided
        if status:
            try:
                StoryStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in StoryStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Validate story points if provided
        if points:
            valid_points = [1, 2, 3, 5, 8, 13, 21]
            if points not in valid_points:
                raise ToolError(f"Story points must be a Fibonacci number: {valid_points}")

        # Prepare update parameters
        update_data = {}
        if title:
            update_data["title"] = title
        if description:
            update_data["description"] = description
        if priority:
            update_data["priority"] = Priority(priority)
        if status:
            update_data["status"] = StoryStatus(status)
        if points is not None:
            update_data["points"] = int(points) if isinstance(points, str) else points
        if tags is not None:
            update_data["tags"] = tags.split(",") if isinstance(tags, str) else tags

        # Check if story service is available
        if self.agent.story_service is None:
            raise ToolError("Story service not available")

        updated_story = self.agent.story_service.update_story(story_id, **update_data)

        if updated_story is None:
            raise ToolError(f"Story with ID {story_id} not found")

        # Format result with story data
        story_data = updated_story.model_dump(mode="json")

        return self.format_result(f"Story '{updated_story.title}' updated successfully", story_data)


class ListStoriesTool(AgileTool):
    """Tool for listing user stories with optional filtering."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for story listing."""
        pass  # Default implementation - no validation

    def apply(self, status: str | None = None, priority: str | None = None, sprint_id: str | None = None) -> ToolResult:
        """List user stories with optional filtering.

        Args:
            status: Filter by status. Options: todo, in_progress, in_review, done, blocked
            priority: Filter by priority. Options: critical, high, medium, low
            sprint_id: Filter by sprint ID (optional)

        Returns:
            Structured data with list of stories
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate status if provided
        if status:
            try:
                StoryStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in StoryStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Validate priority if provided
        if priority:
            try:
                Priority(priority)
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")

        # Convert string filters to enums
        filters = {}
        if status:
            filters["status"] = StoryStatus(status)
        if priority:
            filters["priority"] = Priority(priority)
        if sprint_id:
            filters["sprint_id"] = sprint_id

        # Get filtered stories
        try:
            # Check if story service is available
            if self.agent.story_service is None:
                raise ToolError("Story service not available")
            stories = self.agent.story_service.list_stories(**filters)
        except Exception as err:
            raise RuntimeError("Failed to list stories.") from err

        # Convert stories to dict format
        stories_data = [story.model_dump(mode="json") for story in stories]

        # Build filter description for message
        filter_parts = []
        if status:
            filter_parts.append(f"status '{status}'")
        if priority:
            filter_parts.append(f"priority '{priority}'")
        if sprint_id:
            filter_parts.append(f"sprint '{sprint_id}'")

        filter_desc = f" matching {', '.join(filter_parts)}" if filter_parts else ""

        # Return structured data
        data = {
            "stories": stories_data,
            "count": len(stories),
            "filters": {"status": status, "priority": priority, "sprint_id": sprint_id},
        }

        return self.format_result(f"Found {len(stories)} stories{filter_desc}", data)

    def _format_message_from_data(self, data: dict[str, Any]) -> str:
        """Format human-readable message from story list data.

        This method is deprecated and will be removed. Tools should format
        their own messages when creating ToolResult objects.

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
    """Tool for deleting user stories."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for story deletion."""
        pass  # Default implementation - no validation

    def apply(self, story_id: str) -> ToolResult:
        """Delete a user story by ID.

        Args:
            story_id: The ID of the story to delete (required)

        Returns:
            Success message confirming deletion
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Check if story exists first
        try:
            # Check if story service is available
            if self.agent.story_service is None:
                raise ToolError("Story service not available")

            story = self.agent.story_service.get_story(story_id)
        except Exception as err:
            raise RuntimeError("Failed to load story.") from err

        if story is None:
            raise ToolError(f"Story with ID {story_id} not found")

        # Delete the story
        try:
            # Check if story service is available
            if self.agent.story_service is None:
                raise ToolError("Story service not available")

            success = self.agent.story_service.delete_story(story_id)
        except Exception as err:
            raise RuntimeError("Failed to delete story.") from err

        if not success:
            raise ToolError(f"Failed to delete story with ID {story_id}")

        return self.format_result(
            f"Story '{story.title}' with ID {story_id} deleted successfully",
            {"deleted_story_id": story_id, "deleted_story_title": story.title},
        )
