"""Sprint management tools for Agile MCP Server."""

from datetime import datetime
import json
from typing import Dict, Any, Optional, List

from .base import AgileTool, ToolError, ToolResult
from ..models.sprint import SprintStatus


class CreateSprintTool(AgileTool):
    """Create a new sprint in the agile project."""

    def apply(
        self,
        name: str,
        goal: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> ToolResult:
        """Create a new sprint.

        Args:
            name: Sprint name (required)
            goal: Sprint goal or objective (optional)
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            tags: Comma-separated tags (optional)

        Returns:
            Success message with sprint details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Parse and validate dates
        start_date_obj = None
        end_date_obj = None

        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError(f"Invalid start_date format: {start_date}. Use YYYY-MM-DD format.")

        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError(f"Invalid end_date format: {end_date}. Use YYYY-MM-DD format.")

        # Validate date range
        if start_date_obj and end_date_obj and end_date_obj <= start_date_obj:
            raise ToolError("End date must be after start date")

        # Parse tags
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]

        # Create the sprint
        sprint = self.agent.sprint_service.create_sprint(
            name=name, goal=goal, start_date=start_date_obj, end_date=end_date_obj, tags=tags_list
        )

        # Format result with sprint data
        sprint_data = sprint.model_dump(mode="json")

        return self.format_result(
            f"Sprint '{sprint.name}' created successfully with ID {sprint.id}",
            sprint_data
        )


class GetSprintTool(AgileTool):
    """Retrieve a sprint by its ID."""

    def apply(self, sprint_id: str) -> ToolResult:
        """Get a sprint by ID.

        Args:
            sprint_id: The ID of the sprint to retrieve (required)

        Returns:
            Success message with sprint details
        """
        # Check if project is initialized
        self._check_project_initialized()

        sprint = self.agent.sprint_service.get_sprint(sprint_id)

        if sprint is None:
            raise ToolError(f"Sprint with ID {sprint_id} not found")

        # Get progress information
        progress = self.agent.sprint_service.get_sprint_progress(sprint_id)

        # Convert datetime objects to strings for JSON serialization
        if "start_date" in progress and progress["start_date"]:
            progress["start_date"] = progress["start_date"].isoformat()
        if "end_date" in progress and progress["end_date"]:
            progress["end_date"] = progress["end_date"].isoformat()

        # Format result with sprint data and progress
        sprint_data = sprint.model_dump(mode="json")
        data = {"sprint": sprint_data, "progress": progress}

        return self.format_result(
            f"Retrieved sprint: {sprint.name} (ID: {sprint.id}, Status: {sprint.status.value})",
            data
        )


class ListSprintsTool(AgileTool):
    """List sprints with optional filtering."""

    def apply(self, status: Optional[str] = None, include_stories: Optional[bool] = False) -> ToolResult:
        """List sprints with optional filtering.

        Args:
            status: Filter by status. Options: SprintStatus.PLANNING, SprintStatus.ACTIVE, SprintStatus.COMPLETED, SprintStatus.CANCELLED
            include_stories: Include story IDs in results (optional: true/false, default: false)

        Returns:
            Structured data with list of sprints
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate and parse status filter
        status_enum = None
        if status:
            try:
                status_enum = SprintStatus(status.lower())
            except ValueError:
                valid_statuses = [s.value for s in SprintStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Get filtered sprints
        sprints = self.agent.sprint_service.list_sprints(status=status_enum, include_story_ids=include_stories)

        # Convert sprints to dict format
        sprints_data = [sprint.model_dump(mode="json") for sprint in sprints]

        # Build filter description for message
        status_filter_msg = f" with status '{status_enum.value}'" if status_enum else ""
        stories_msg = " (including stories)" if include_stories else ""

        # Return structured data
        data = {
            "sprints": sprints_data,
            "count": len(sprints_data),
            "filters": {"status": status_enum.value if status_enum else None, "include_stories": include_stories},
        }

        return self.format_result(
            f"Found {len(sprints_data)} sprints{status_filter_msg}{stories_msg}",
            data
        )

    def _format_message_from_data(self, data: Dict[str, Any]) -> str:
        """Format human-readable message from sprint list data.

        This method is deprecated and will be removed. Tools should format
        their own messages when creating ToolResult objects.

        Args:
            data: Structured sprint list data

        Returns:
            Human-readable message string
        """
        count = data.get("count", 0)
        filters = data.get("filters", {})

        if count == 0:
            return "No sprints found matching the specified criteria"

        # Build filter description
        status_filter_msg = f" with status '{filters.get('status')}'" if filters.get("status") else ""
        stories_msg = " (including stories)" if filters.get("include_stories") else ""

        return f"Found {count} sprints{status_filter_msg}{stories_msg}"


class UpdateSprintTool(AgileTool):
    """Update an existing sprint."""

    def apply(
        self,
        sprint_id: str,
        name: Optional[str] = None,
        goal: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> ToolResult:
        """Update an existing sprint.

        Args:
            sprint_id: The ID of the sprint to update (required)
            name: New sprint name (optional)
            goal: New sprint goal (optional)
            status: New status. Options: SprintStatus.PLANNING, SprintStatus.ACTIVE, SprintStatus.COMPLETED, SprintStatus.CANCELLED
            start_date: New start date in YYYY-MM-DD format (optional)
            end_date: New end date in YYYY-MM-DD format (optional)
            tags: New comma-separated tags (optional)

        Returns:
            Success message with updated sprint details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Prepare update parameters
        update_params = {}

        if name:
            update_params["name"] = name

        if goal:
            update_params["goal"] = goal

        if status:
            try:
                update_params["status"] = SprintStatus(status.lower())
            except ValueError:
                valid_statuses = [s.value for s in SprintStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        if start_date:
            try:
                update_params["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError(f"Invalid start_date format: {start_date}. Use YYYY-MM-DD format.")

        if end_date:
            try:
                update_params["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError(f"Invalid end_date format: {end_date}. Use YYYY-MM-DD format.")

        if tags:
            update_params["tags"] = [tag.strip() for tag in tags.split(",")]

        # Update the sprint
        updated_sprint = self.agent.sprint_service.update_sprint(sprint_id, **update_params)

        if updated_sprint is None:
            raise ToolError(f"Sprint with ID {sprint_id} not found")

        # Format result with sprint data
        sprint_data = updated_sprint.model_dump(mode="json")

        return self.format_result(
            f"Sprint '{updated_sprint.name}' updated successfully",
            sprint_data
        )


class ManageSprintStoriesTool(AgileTool):
    """Add or remove stories from a sprint."""

    def apply(self, sprint_id: str, action: str, story_id: str) -> ToolResult:
        """Add or remove stories from a sprint.

        Args:
            sprint_id: The sprint ID (required)
            action: Action to perform. Options: Literal["add", "remove"]
            story_id: The story ID to add or remove (required)

        Returns:
            Success message with updated sprint details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate action
        if action not in ["add", "remove"]:
            raise ToolError("Action must be either 'add' or 'remove'")

        if action == "add":
            updated_sprint = self.agent.sprint_service.add_story_to_sprint(sprint_id, story_id)
            action_message = f"Story '{story_id}' added to sprint '{sprint_id}'"
        else:  # action == "remove"
            updated_sprint = self.agent.sprint_service.remove_story_from_sprint(sprint_id, story_id)
            action_message = f"Story '{story_id}' removed from sprint '{sprint_id}'"

        if updated_sprint is None:
            raise ToolError(f"Sprint with ID '{sprint_id}' not found")

        # Format result with sprint data
        sprint_data = {
            "id": updated_sprint.id,
            "name": updated_sprint.name,
            "story_ids": updated_sprint.story_ids,
            "story_count": len(updated_sprint.story_ids),
            "action": action,
            "story_id": story_id
        }

        return self.format_result(action_message, sprint_data)


class GetSprintProgressTool(AgileTool):
    """Get detailed progress information for a sprint."""

    def apply(self, sprint_id: str) -> ToolResult:
        """Get detailed progress information for a sprint.

        Args:
            sprint_id: The sprint ID to get progress for (required)

        Returns:
            Success message with progress details
        """
        # Check if project is initialized
        self._check_project_initialized()

        sprint = self.agent.sprint_service.get_sprint(sprint_id)
        if sprint is None:
            raise ToolError(f"Sprint with ID '{sprint_id}' not found")

        progress = self.agent.sprint_service.get_sprint_progress(sprint_id)

        # Convert datetime objects to strings for JSON serialization
        if "start_date" in progress and progress["start_date"]:
            progress["start_date"] = progress["start_date"].isoformat()
        if "end_date" in progress and progress["end_date"]:
            progress["end_date"] = progress["end_date"].isoformat()

        # Calculate duration if possible
        duration_info = {}
        duration = self.agent.sprint_service.calculate_sprint_duration(sprint_id)
        if duration:
            duration_info = {"total_days": duration.days, "total_hours": duration.total_seconds() / 3600}

        # Format result with progress data
        data = {"progress": progress, "duration": duration_info}

        status_message = f"Sprint '{progress.get('name', sprint_id)}' progress: {progress.get('status', 'unknown')}"
        if "time_progress_percent" in progress:
            status_message += f" ({progress['time_progress_percent']:.1f}% time elapsed)"

        return self.format_result(status_message, data)


class GetActiveSprintTool(AgileTool):
    """Get the currently active sprint."""

    def apply(self) -> ToolResult:
        """Get the currently active sprint.

        Returns:
            Success message with active sprint details
        """
        # Check if project is initialized
        self._check_project_initialized()

        active_sprint = self.agent.sprint_service.get_active_sprint()

        if active_sprint is None:
            return self.format_result(
                "No active sprint found",
                {"active_sprint": None}
            )

        # Get progress information
        progress = self.agent.sprint_service.get_sprint_progress(active_sprint.id)

        # Convert datetime objects to strings for JSON serialization
        if "start_date" in progress and progress["start_date"]:
            progress["start_date"] = progress["start_date"].isoformat()
        if "end_date" in progress and progress["end_date"]:
            progress["end_date"] = progress["end_date"].isoformat()

        # Format result with active sprint data
        active_sprint_data = active_sprint.model_dump(mode="json")
        data = {"active_sprint": active_sprint_data, "progress": progress}

        return self.format_result(
            f"Active sprint: {active_sprint.name} (ID: {active_sprint.id}, {len(active_sprint.story_ids)} stories)",
            data
        )
