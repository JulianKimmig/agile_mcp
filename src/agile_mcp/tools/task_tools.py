"""Task management tools for Agile MCP Server."""

from datetime import datetime

from ..models.task import TaskPriority, TaskStatus
from .base import AgileTool, ToolError, ToolResult


class CreateTaskTool(AgileTool):
    """Tool for creating new tasks."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for task creation."""
        pass  # Default implementation - no validation

    def apply(
        self,
        title: str,
        description: str,
        story_id: str | None = None,
        priority: str = "medium",
        assignee: str | None = None,
        estimated_hours: float | None = None,
        due_date: str | None = None,
        dependencies: str | None = None,
        tags: str | None = None,
    ) -> ToolResult:
        """Create a new task.

        Args:
            title: Task title (required)
            description: Task description (required)
            story_id: ID of the parent story (optional)
            priority: Task priority. Options: TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL
            assignee: Person assigned to this task (optional)
            estimated_hours: Estimated hours to complete (optional)
            due_date: Task due date in YYYY-MM-DD format (optional)
            dependencies: Comma-separated task IDs this task depends on (optional)
            tags: Comma-separated tags (optional)

        Returns:
            Success message with task details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate priority
        try:
            priority_enum = TaskPriority(priority)
        except ValueError:
            valid_priorities = [p.value for p in TaskPriority]
            raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")

        # Validate estimated hours if provided
        if estimated_hours and estimated_hours < 0:
            raise ToolError("Estimated hours must be non-negative")

        # Parse due date if provided
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError("Due date must be in YYYY-MM-DD format")

        # Parse dependencies if provided
        dependencies_list = []
        if dependencies:
            dependencies_list = [dep.strip() for dep in dependencies.split(",")]

        # Parse tags if provided
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]

        # Create the task
        try:
            task = self.agent.task_service.create_task(
                title=title,
                description=description,
                story_id=story_id,
                priority=priority_enum,
                assignee=assignee,
                estimated_hours=estimated_hours,
                due_date=due_date_obj,
                dependencies=dependencies_list,
                tags=tags_list,
            )
        except Exception as err:
            raise RuntimeError("Failed to perform task operation.") from err

        # Format result with task data
        task_data = task.model_dump(mode="json")

        return self.format_result(f"Task '{task.title}' created successfully with ID {task.id}", task_data)


class GetTaskTool(AgileTool):
    """Tool for retrieving tasks."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for task retrieval."""
        pass  # Default implementation - no validation

    def apply(self, task_id: str) -> ToolResult:
        """Get a task by ID.

        Args:
            task_id: The ID of the task to retrieve (required)

        Returns:
            Success message with task details
        """
        # Check if project is initialized
        self._check_project_initialized()

        task = self.agent.task_service.get_task(task_id)

        if task is None:
            raise ToolError(f"Task with ID {task_id} not found")

        # Format result with task data
        task_data = task.model_dump(mode="json")

        return self.format_result(f"Retrieved task: {task.title} (ID: {task.id})", task_data)


class UpdateTaskTool(AgileTool):
    """Tool for updating existing tasks."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for task update."""
        pass  # Default implementation - no validation

    def apply(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee: str | None = None,
        estimated_hours: float | None = None,
        actual_hours: float | None = None,
        due_date: str | None = None,
        dependencies: str | None = None,
        tags: str | None = None,
    ) -> ToolResult:
        """Update an existing task.

        Args:
            task_id: The ID of the task to update (required)
            title: New task title (optional)
            description: New task description (optional)
            status: New status. Options: TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED
            priority: New priority. Options: TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL
            assignee: New assignee (optional)
            estimated_hours: New estimated hours (optional)
            actual_hours: Actual hours spent (optional)
            due_date: New due date in YYYY-MM-DD format (optional)
            dependencies: New comma-separated dependencies (optional)
            tags: New comma-separated tags (optional)

        Returns:
            Success message with updated task details
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate status if provided
        if status:
            try:
                TaskStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        # Validate priority if provided
        if priority:
            try:
                TaskPriority(priority)
            except ValueError:
                valid_priorities = [p.value for p in TaskPriority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")

        # Validate hours if provided
        if estimated_hours and estimated_hours < 0:
            raise ToolError("Estimated hours must be non-negative")
        if actual_hours and actual_hours < 0:
            raise ToolError("Actual hours must be non-negative")

        # Prepare update parameters
        update_params = {}
        if title:
            update_params["title"] = title
        if description:
            update_params["description"] = description
        if status:
            update_params["status"] = TaskStatus(status)
        if priority:
            update_params["priority"] = TaskPriority(priority)
        if assignee:
            update_params["assignee"] = assignee
        if estimated_hours:
            update_params["estimated_hours"] = estimated_hours
        if actual_hours:
            update_params["actual_hours"] = actual_hours
        if due_date:
            try:
                update_params["due_date"] = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError("Due date must be in YYYY-MM-DD format")
        if dependencies:
            update_params["dependencies"] = [dep.strip() for dep in dependencies.split(",")]
        if tags:
            update_params["tags"] = [tag.strip() for tag in tags.split(",")]

        # Update the task
        try:
            updated_task = self.agent.task_service.update_task(task_id, **update_params)
        except Exception as err:
            raise RuntimeError("Failed to perform task operation.") from err

        if updated_task is None:
            raise ToolError(f"Task with ID {task_id} not found")

        # Format result with task data
        task_data = updated_task.model_dump(mode="json")

        return self.format_result(f"Task '{updated_task.title}' updated successfully", task_data)


class DeleteTaskTool(AgileTool):
    """Tool for deleting tasks."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for task deletion."""
        pass  # Default implementation - no validation

    def apply(self, task_id: str) -> ToolResult:
        """Delete a task by ID.

        Args:
            task_id: The ID of the task to delete (required)

        Returns:
            Success message confirming deletion
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Check if task exists first
        task = self.agent.task_service.get_task(task_id)
        if task is None:
            raise ToolError(f"Task with ID {task_id} not found")

        # Delete the task
        try:
            deleted = self.agent.task_service.delete_task(task_id)
        except Exception as err:
            raise RuntimeError("Failed to perform task operation.") from err

        if not deleted:
            raise ToolError(f"Failed to delete task with ID {task_id}")

        return self.format_result(
            f"Task '{task.title}' (ID: {task_id}) deleted successfully",
            {"deleted_task_id": task_id, "deleted_task_title": task.title},
        )


class ListTasksTool(AgileTool):
    """Tool for listing tasks with optional filtering."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters for task listing."""
        pass  # Default implementation - no validation

    def apply(
        self,
        story_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee: str | None = None,
        include_completed: bool = True,
    ) -> ToolResult:
        """List tasks with optional filtering.

        Args:
            story_id: Filter by story ID (optional)
            status: Filter by status. Options: TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED
            priority: Filter by priority. Options: TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH, TaskPriority.CRITICAL
            assignee: Filter by assignee (optional)
            include_completed: Include completed tasks (optional, default: true)

        Returns:
            Success message with list of tasks
        """
        # Check if project is initialized
        self._check_project_initialized()

        # Validate filters
        if status:
            try:
                TaskStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")

        if priority:
            try:
                TaskPriority(priority)
            except ValueError:
                valid_priorities = [p.value for p in TaskPriority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")

        # Get filtered tasks
        try:
            tasks = self.agent.task_service.list_tasks(
                story_id=story_id,
                status=TaskStatus(status) if status else None,
                priority=TaskPriority(priority) if priority else None,
                assignee=assignee,
                include_completed=include_completed,
            )
        except Exception as err:
            raise RuntimeError("Failed to perform task operation.") from err

        # Format result
        tasks_data = [task.model_dump(mode="json") for task in tasks]

        # Build filter description for message
        filter_parts = []
        if story_id:
            filter_parts.append(f"story '{story_id}'")
        if status:
            filter_parts.append(f"status '{status}'")
        if priority:
            filter_parts.append(f"priority '{priority}'")
        if assignee:
            filter_parts.append(f"assignee '{assignee}'")
        if not include_completed:
            filter_parts.append("excluding completed")

        filter_desc = f" matching {', '.join(filter_parts)}" if filter_parts else ""

        data = {"tasks": tasks_data, "count": len(tasks)}

        return self.format_result(f"Found {len(tasks)} tasks{filter_desc}", data)
