"""Epic management tools for Agile MCP Server."""

import json
from typing import Dict, Any, Optional, List

from .base import AgileTool, ToolError, ToolResult
from ..models.epic import EpicStatus


class CreateEpicTool(AgileTool):
    """Create a new epic in the agile project."""

    def apply(self, title: str, description: str, status: str = "planning", tags: Optional[str] = None) -> ToolResult:
        """Create a new epic.

        Args:
            title: Epic title (required)
            description: Epic description (required)
            status: Epic status. Options: EpicStatus.PLANNING, EpicStatus.IN_PROGRESS, EpicStatus.COMPLETED, EpicStatus.ON_HOLD
            tags: Comma-separated tags (optional)

        Returns:
            Success message with epic details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate status
        try:
            status_enum = EpicStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in EpicStatus]
            raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Parse tags if provided
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]

        # Create the epic
        epic = self.agent.epic_service.create_epic(
            title=title, description=description, status=status_enum, tags=tags_list
        )

        # Format result with epic data
        epic_data = epic.model_dump(mode="json")

        return self.format_result(
            f"Epic '{epic.title}' created successfully with ID {epic.id}",
            epic_data
        )


class GetEpicTool(AgileTool):
    """Retrieve an epic by its ID."""

    def apply(self, epic_id: str) -> ToolResult:
        """Get an epic by ID.

        Args:
            epic_id: The ID of the epic to retrieve (required)

        Returns:
            Success message with epic details
        """
        # Check if project is initialized
        self._check_project_initialized()

        epic = self.agent.epic_service.get_epic(epic_id)

        if epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Format result with epic data
        epic_data = epic.model_dump(mode="json")

        return self.format_result(
            f"Retrieved epic: {epic.title} (ID: {epic.id})",
            epic_data
        )


class UpdateEpicTool(AgileTool):
    """Update an existing epic."""

    def apply(
        self,
        epic_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> ToolResult:
        """Update an existing epic.

        Args:
            epic_id: The ID of the epic to update (required)
            title: New epic title (optional)
            description: New epic description (optional)
            status: New status. Options: EpicStatus.PLANNING, EpicStatus.IN_PROGRESS, EpicStatus.COMPLETED, EpicStatus.ON_HOLD
            tags: New comma-separated tags (optional)

        Returns:
            Success message with updated epic details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate status if provided
        if status:
            try:
                EpicStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in EpicStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Prepare update parameters
        update_params = {}
        if title:
            update_params["title"] = title
        if description:
            update_params["description"] = description
        if status:
            update_params["status"] = EpicStatus(status)
        if tags:
            update_params["tags"] = [tag.strip() for tag in tags.split(",")]

        # Update the epic
        updated_epic = self.agent.epic_service.update_epic(epic_id, **update_params)

        if updated_epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Format result with epic data
        epic_data = updated_epic.model_dump(mode="json")

        return self.format_result(
            f"Epic '{updated_epic.title}' updated successfully",
            epic_data
        )


class DeleteEpicTool(AgileTool):
    """Delete an epic from the agile project."""

    def apply(self, epic_id: str) -> ToolResult:
        """Delete an epic by ID.

        Args:
            epic_id: The ID of the epic to delete (required)

        Returns:
            Success message confirming deletion
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Check if epic exists first
        epic = self.agent.epic_service.get_epic(epic_id)
        if epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Delete the epic
        deleted = self.agent.epic_service.delete_epic(epic_id)

        if not deleted:
            raise ToolError(f"Failed to delete epic with ID {epic_id}")

        return self.format_result(
            f"Epic '{epic.title}' (ID: {epic_id}) deleted successfully",
            {"deleted_epic_id": epic_id, "deleted_epic_title": epic.title}
        )


class ListEpicsTool(AgileTool):
    """List epics with optional filtering."""

    def apply(self, status: Optional[str] = None, include_stories: bool = False) -> ToolResult:
        """List epics with optional filtering.

        Args:
            status: Filter by status. Options: EpicStatus.PLANNING, EpicStatus.IN_PROGRESS, EpicStatus.COMPLETED, EpicStatus.ON_HOLD
            include_stories: Include story IDs in results (optional, default: false)

        Returns:
            Success message with list of epics
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate status filter
        if status:
            try:
                EpicStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in EpicStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Get filtered epics
        epics = self.agent.epic_service.list_epics(
            status=EpicStatus(status) if status else None, include_story_ids=include_stories
        )

        # Format result
        epics_data = [epic.model_dump(mode="json") for epic in epics]
        
        # Build filter description for message
        filter_desc = f" with status '{status}'" if status else ""
        stories_desc = " (including stories)" if include_stories else ""

        data = {"epics": epics_data, "count": len(epics)}

        return self.format_result(
            f"Found {len(epics)} epics{filter_desc}{stories_desc}",
            data
        )


class ManageEpicStoriesTool(AgileTool):
    """Add or remove stories from an epic."""

    def apply(self, epic_id: str, action: str, story_id: str) -> ToolResult:
        """Add or remove stories from an epic.

        Args:
            epic_id: The epic ID (required)
            action: Action to perform. Options: Literal["add", "remove"]
            story_id: The story ID to add or remove (required)

        Returns:
            Success message with updated epic details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate action
        if action not in ["add", "remove"]:
            raise ToolError("Action must be either 'add' or 'remove'")

        # Perform the action
        if action == "add":
            updated_epic = self.agent.epic_service.add_story_to_epic(epic_id, story_id)
            action_msg = "added to"
        else:  # remove
            updated_epic = self.agent.epic_service.remove_story_from_epic(epic_id, story_id)
            action_msg = "removed from"

        if updated_epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Format result with epic data
        epic_data = updated_epic.model_dump(mode="json")

        return self.format_result(
            f"Story '{story_id}' {action_msg} epic '{updated_epic.title}'",
            {
                "epic": epic_data,
                "action": action,
                "story_id": story_id
            }
        )


class GetProductBacklogTool(AgileTool):
    """Get the product backlog - all stories not assigned to a sprint."""

    def apply(self, priority: Optional[str] = None, tags: Optional[str] = None, include_completed: bool = False) -> ToolResult:
        """Get the product backlog with optional filtering.

        Args:
            priority: Filter by priority. Options: Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL
            tags: Filter by comma-separated tags (optional)
            include_completed: Include completed stories (optional, default: false)

        Returns:
            Success message with product backlog
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Get all stories not assigned to sprints
        backlog_stories = self.agent.story_service.list_stories(_filter_no_sprint=True)

        # Apply filters
        if priority:
            from ..models.story import Priority

            try:
                priority_enum = Priority(priority)
                backlog_stories = [s for s in backlog_stories if s.priority == priority_enum]
            except ValueError:
                valid_priorities = [p.value for p in Priority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")

        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(",")]
            backlog_stories = [
                s for s in backlog_stories if any(tag in [t.lower() for t in s.tags] for tag in tag_list)
            ]

        if not include_completed:
            from ..models.story import StoryStatus

            backlog_stories = [s for s in backlog_stories if s.status != StoryStatus.DONE]

        # Sort by priority (high to low) then by creation date
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        backlog_stories.sort(key=lambda s: (priority_order.get(s.priority.value, 0), s.created_at), reverse=True)

        # Format result
        stories_data = [story.model_dump(mode="json") for story in backlog_stories]
        
        # Calculate total points
        total_points = sum(story.points for story in backlog_stories if story.points)

        # Build filter description for message
        filter_parts = []
        if priority:
            filter_parts.append(f"priority '{priority}'")
        if tags:
            filter_parts.append(f"tags '{tags}'")
        if not include_completed:
            filter_parts.append("excluding completed")

        filter_desc = f" matching {', '.join(filter_parts)}" if filter_parts else ""

        data = {
            "backlog_stories": stories_data, 
            "count": len(backlog_stories),
            "total_points": total_points,
            "filters": {
                "priority": priority,
                "tags": tags,
                "include_completed": include_completed
            }
        }

        return self.format_result(
            f"Product Backlog: {len(backlog_stories)} stories ({total_points} total points){filter_desc}",
            data
        )
