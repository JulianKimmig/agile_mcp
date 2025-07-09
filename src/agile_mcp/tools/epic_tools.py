"""Epic management tools for Agile MCP Server."""

from ..models.epic import EpicStatus
from .base import AgileTool, ToolError, ToolResult


class CreateEpicTool(AgileTool):
    """Tool for creating new epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic creation."""
        pass  # Default implementation - no validation

    """Create a new epic in the agile project."""

    def apply(self, name: str, description: str, status: str = "planning", tags: str | None = None) -> ToolResult:
        """Create a new epic.

        Args:
            name: Epic name (required)
            description: Epic description (required)
            status: Epic status. Options: planning, in_progress, completed, cancelled
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
        try:
            if self.agent.epic_service is None:
                raise ToolError("Epic service is not initialized.")
            epic = self.agent.epic_service.create_epic(
                name=name, description=description, status=status_enum, tags=tags_list
            )
        except Exception as err:
            raise RuntimeError("Failed to perform epic operation.") from err

        # Format result with epic data
        epic_data = epic.model_dump(mode="json")
        epic_data["status"] = epic.status.value

        return self.format_result(f"Epic '{epic.name}' created successfully with ID {epic.id}", epic_data)


class GetEpicTool(AgileTool):
    """Tool for retrieving epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic retrieval."""
        pass  # Default implementation - no validation

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

        if self.agent.epic_service is None:
            raise ToolError("Epic service is not initialized.")
        epic = self.agent.epic_service.get_epic(epic_id)

        if epic:
            epic_data = epic.model_dump(mode="json")
            epic_data["status"] = epic.status.value
            return self.format_result(f"Retrieved epic: {epic.name} (ID: {epic.id})", epic_data)
        else:
            return self.format_error(f"Epic with ID {epic_id} not found")


class UpdateEpicTool(AgileTool):
    """Tool for updating existing epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic update."""
        pass  # Default implementation - no validation

    """Update an existing epic."""

    def apply(
        self,
        epic_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        tags: str | None = None,
    ) -> ToolResult:
        """Update an existing epic.

        Args:
            epic_id: The ID of the epic to update (required)
            name: New epic name (optional)
            description: New epic description (optional)
            status: New status. Options: planning, in_progress, completed, cancelled
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
        if name:
            update_params["name"] = name
        if description:
            update_params["description"] = description
        if status:
            update_params["status"] = EpicStatus(status)
        if tags:
            update_params["tags"] = [tag.strip() for tag in tags.split(",")]

        # Update the epic
        try:
            if self.agent.epic_service is None:
                raise ToolError("Epic service is not initialized.")
            updated_epic = self.agent.epic_service.update_epic(epic_id, **update_params)
        except Exception as err:
            raise RuntimeError("Failed to perform epic operation.") from err

        if updated_epic:
            epic_data = updated_epic.model_dump(mode="json")
            epic_data["status"] = updated_epic.status.value
            return self.format_result(f"Epic '{updated_epic.name}' updated successfully", epic_data)
        else:
            return self.format_error(f"Failed to update epic with ID {epic_id}")


class DeleteEpicTool(AgileTool):
    """Tool for deleting epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic deletion."""
        pass  # Default implementation - no validation

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
        if self.agent.epic_service is None:
            raise ToolError("Epic service is not initialized.")
        epic = self.agent.epic_service.get_epic(epic_id)
        if epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Delete the epic
        try:
            if self.agent.epic_service is None:
                raise ToolError("Epic service is not initialized.")
            deleted = self.agent.epic_service.delete_epic(epic_id)
        except Exception as err:
            raise RuntimeError("Failed to perform epic operation.") from err

        if not deleted:
            raise ToolError(f"Failed to delete epic with ID {epic_id}")

        return self.format_result(
            f"Epic '{epic.name}' (ID: {epic_id}) deleted successfully",
            {"epic_id": epic_id, "deleted": True},
        )


class ListEpicsTool(AgileTool):
    """Tool for listing epics with optional filtering."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic listing."""
        pass  # Default implementation - no validation

    """List epics with optional filtering."""

    def apply(self, status: str | None = None, include_stories: bool = False) -> ToolResult:
        """List epics with optional filtering.

        Args:
            status: Filter by status. Options: planning, in_progress, completed, cancelled
            include_stories: Include story IDs in results (optional, default: false)

        Returns:
            Success message with list of epics
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate status filter
        status_enum = None
        if status:
            try:
                status_enum = EpicStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in EpicStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Get epics first
        if self.agent.epic_service is None:
            raise ToolError("Epic service not available")

        epics = self.agent.epic_service.list_epics(status=status_enum)

        # Format result
        epic_list = []
        for epic in epics:
            epic_line = f"- {epic.id}: {epic.name} ({epic.status.value})"
            if include_stories and epic.story_ids:
                epic_line += f" (Stories: {', '.join(epic.story_ids)})"
            epic_list.append(epic_line)

        # Build message with epic details
        if not epics:
            message = "No epics found matching the specified criteria"
        else:
            # Build message with epic listings
            epic_lines = []
            for epic in epics:
                story_count = len(epic.story_ids) if epic.story_ids else 0
                epic_line = f"- {epic.id}: {epic.name} ({epic.status.value})"
                if story_count > 0:
                    epic_line += f" ({story_count} stories)"
                epic_lines.append(epic_line)

            # Build filter description for message
            filter_desc = f" with status '{status}'" if status else ""
            stories_desc = " (including stories)" if include_stories else ""

            message = f"Found {len(epics)} epics{filter_desc}{stories_desc}\n" + "\n".join(epic_lines)

        data = {"epics": [epic.model_dump(mode="json") for epic in epics], "count": len(epics)}

        return self.format_result(message, data)


class ManageEpicStoriesTool(AgileTool):
    """Tool for managing story assignments to epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic story management."""
        pass  # Default implementation - no validation

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
        try:
            if action == "add":
                if self.agent.epic_service is None:
                    raise ToolError("Epic service is not initialized.")
                updated_epic = self.agent.epic_service.add_story_to_epic(epic_id, story_id)
                action_msg = "added to"
            else:  # remove
                if self.agent.epic_service is None:
                    raise ToolError("Epic service is not initialized.")
                updated_epic = self.agent.epic_service.remove_story_from_epic(epic_id, story_id)
                action_msg = "removed from"
        except Exception as err:
            raise RuntimeError("Failed to perform epic operation.") from err

        if updated_epic:
            return self.format_result(
                f"Story '{story_id}' {action_msg} epic '{updated_epic.name}'",
                {"epic_id": epic_id, "story_id": story_id, "action": action},
            )
        else:
            return self.format_error(f"Failed to update epic with ID {epic_id}")


class GetProductBacklogTool(AgileTool):
    """Tool for retrieving the product backlog."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for product backlog retrieval."""
        pass  # Default implementation - no validation

    """Get the product backlog - all stories not assigned to a sprint."""

    def apply(
        self, priority: str | None = None, tags: str | None = None, include_completed: bool = False
    ) -> ToolResult:
        """Get the product backlog with optional filtering.

        Args:
            priority: Filter by priority. Options: low, Priority.MEDIUM, high, Priority.CRITICAL
            tags: Filter by comma-separated tags (optional)
            include_completed: Include completed stories (optional, default: false)

        Returns:
            Success message with product backlog
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Get all stories not assigned to sprints
        try:
            backlog_stories = self.agent.story_service.list_stories(_filter_no_sprint=True)
        except Exception as err:
            raise RuntimeError("Failed to perform story operation.") from err

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

        # Build message with story details
        if not backlog_stories:
            message = "Product backlog is empty"
        else:
            # Build story listings
            story_lines = []
            for story in backlog_stories:
                points_text = f" ({story.points} pts)" if story.points else ""
                story_line = f"- {story.id}: {story.name} ({story.priority.value}){points_text} [{story.status.value}]"
                story_lines.append(story_line)

            message = (
                f"Product Backlog: {len(backlog_stories)} stories ({total_points} total points){filter_desc}\n"
                + "\n".join(story_lines)
            )

        data = {
            "backlog_stories": stories_data,
            "count": len(backlog_stories),
            "total_points": total_points,
            "filters": {"priority": priority, "tags": tags, "include_completed": include_completed},
        }

        return self.format_result(message, data)
