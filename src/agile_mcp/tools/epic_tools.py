"""Epic management tools for Agile MCP Server."""

from ..models.epic import EpicStatus
from .base import AgileTool, ToolError, ToolResult


class CreateEpicTool(AgileTool):
    """Tool for creating new epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic creation."""
        pass  # Default implementation - no validation

    """Create a new epic in the agile project."""

    def apply(self, title: str, description: str, status: str = "planning", tags: str | None = None) -> ToolResult:
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
        try:
            if self.agent.epic_service is None:
                raise ToolError("Epic service is not initialized.")
            epic = self.agent.epic_service.create_epic(
                title=title, description=description, status=status_enum, tags=tags_list
            )
        except Exception as err:
            raise RuntimeError("Failed to perform epic operation.") from err

        # Format result with epic data
        epic_data = epic.model_dump(mode="json")

        return self.format_result(f"Epic '{epic.title}' created successfully with ID {epic.id}", epic_data)


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

        if epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Format result with epic data
        epic_data = epic.model_dump(mode="json")

        return self.format_result(f"Retrieved epic: {epic.title} (ID: {epic.id})", epic_data)


class UpdateEpicTool(AgileTool):
    """Tool for updating existing epics."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for epic update."""
        pass  # Default implementation - no validation

    """Update an existing epic."""

    def apply(
        self,
        epic_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        tags: str | None = None,
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
        try:
            if self.agent.epic_service is None:
                raise ToolError("Epic service is not initialized.")
            updated_epic = self.agent.epic_service.update_epic(epic_id, **update_params)
        except Exception as err:
            raise RuntimeError("Failed to perform epic operation.") from err

        if updated_epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Format result with epic data
        epic_data = updated_epic.model_dump(mode="json")

        return self.format_result(f"Epic '{updated_epic.title}' updated successfully", epic_data)


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
            f"Epic '{epic.title}' (ID: {epic_id}) deleted successfully",
            {"deleted_epic_id": epic_id, "deleted_epic_title": epic.title},
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
                status_enum = EpicStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in EpicStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Get epics first
        if self.agent.epic_service is None:
            raise ToolError("Epic service not available")

        epics = self.agent.epic_service.list_epics(status=status_enum)

        # Get stories if requested - note: currently not used in output
        # This could be extended in the future to show story details
        if include_stories and self.agent.story_service is not None:
            try:
                _ = self.agent.story_service.list_stories()
                # stories_data = [story.model_dump(mode="json") for story in stories]
                # Could be used to enrich epic data with story details
            except Exception:
                # If story service fails, just continue without stories
                pass

        # Format result
        epics_data = [epic.model_dump(mode="json") for epic in epics]

        # Build filter description for message
        filter_desc = f" with status '{status}'" if status else ""
        stories_desc = " (including stories)" if include_stories else ""

        data = {"epics": epics_data, "count": len(epics)}

        return self.format_result(f"Found {len(epics)} epics{filter_desc}{stories_desc}", data)


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

        if updated_epic is None:
            raise ToolError(f"Epic with ID {epic_id} not found")

        # Format result with epic data
        epic_data = updated_epic.model_dump(mode="json")

        return self.format_result(
            f"Story '{story_id}' {action_msg} epic '{updated_epic.title}'",
            {"epic": epic_data, "action": action, "story_id": story_id},
        )


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
            priority: Filter by priority. Options: Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL
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

        data = {
            "backlog_stories": stories_data,
            "count": len(backlog_stories),
            "total_points": total_points,
            "filters": {"priority": priority, "tags": tags, "include_completed": include_completed},
        }

        return self.format_result(
            f"Product Backlog: {len(backlog_stories)} stories ({total_points} total points){filter_desc}", data
        )
