"""Task service for Agile MCP Server."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.task import Task, TaskStatus, TaskPriority
from ..storage.filesystem import AgileProjectManager
from ..utils.id_generator import generate_task_id


class TaskService:
    """Service for managing tasks within user stories."""

    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the task service.

        Args:
            project_manager: The project manager instance
        """
        self.project_manager = project_manager
        self.tasks_dir = project_manager.get_tasks_dir()

    def create_task(
        self,
        title: str,
        description: str,
        story_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        status: Optional[TaskStatus] = None,
        validate_story: bool = False,
    ) -> Task:
        """Create a new task.

        Args:
            title: Task title
            description: Task description
            story_id: ID of the parent story (optional)
            priority: Task priority
            assignee: Person assigned to the task
            estimated_hours: Estimated hours to complete
            due_date: Task due date
            dependencies: List of task IDs this task depends on
            tags: Task tags
            status: Task status
            validate_story: Whether to validate that the story exists

        Returns:
            Created task instance

        Raises:
            ValueError: If story doesn't exist (when validate_story=True) or validation fails
        """
        # Validate estimated hours
        if estimated_hours and estimated_hours < 0:
            raise ValueError("Estimated hours must be non-negative")

        # Verify story exists if provided and validation is enabled
        if validate_story and story_id:
            story = self.project_manager.get_story(story_id)
            if not story:
                raise ValueError(f"Story with ID {story_id} not found")

        # Validate dependencies exist
        if dependencies:
            for dep_id in dependencies:
                dep_task = self.project_manager.get_task(dep_id)
                if not dep_task:
                    raise ValueError(f"Dependency task with ID {dep_id} not found")

        # Generate unique task ID
        task_id = generate_task_id()

        task = Task(
            id=task_id,
            title=title,
            description=description,
            story_id=story_id,
            priority=priority,
            assignee=assignee,
            estimated_hours=estimated_hours,
            due_date=due_date,
            dependencies=dependencies or [],
            tags=tags or [],
            status=status or TaskStatus.TODO,
        )

        # Save task
        self.project_manager.save_task(task)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        return self.project_manager.get_task(task_id)

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee: Optional[str] = None,
        estimated_hours: Optional[float] = None,
        actual_hours: Optional[float] = None,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Task]:
        """Update an existing task.

        Args:
            task_id: Task ID
            title: New title
            description: New description
            status: New status
            priority: New priority
            assignee: New assignee
            estimated_hours: New estimated hours
            actual_hours: Actual hours spent
            due_date: New due date
            dependencies: New dependencies
            tags: New tags

        Returns:
            Updated task if found, None otherwise
        """
        task = self.project_manager.get_task(task_id)
        if not task:
            return None

        # Validate estimated hours if provided
        if estimated_hours and estimated_hours < 0:
            raise ValueError("Estimated hours must be non-negative")

        # Validate dependencies if provided
        if dependencies:
            for dep_id in dependencies:
                if dep_id == task_id:
                    raise ValueError("Task cannot depend on itself")
                dep_task = self.project_manager.get_task(dep_id)
                if not dep_task:
                    raise ValueError(f"Dependency task with ID {dep_id} not found")

        # Update fields
        if title:
            task.title = title
        if description:
            task.description = description
        if status:
            task.status = status
        if priority:
            task.priority = priority
        if assignee:
            task.assignee = assignee
        if estimated_hours:
            task.estimated_hours = estimated_hours
        if actual_hours:
            task.actual_hours = actual_hours
        if due_date:
            task.due_date = due_date
        if dependencies:
            task.dependencies = dependencies
        if tags:
            task.tags = tags

        task.updated_at = datetime.now()

        # Save updated task
        self.project_manager.save_task(task)

        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if task was deleted, False if not found
        """
        task = self.project_manager.get_task(task_id)
        if not task:
            return False

        # Check if other tasks depend on this one
        dependent_tasks: List[Task] = []
        if task.story_id:
            dependent_tasks = self.get_tasks_by_story(task.story_id)
        for dep_task in dependent_tasks:
            if task_id in dep_task.dependencies:
                raise ValueError(f"Cannot delete task {task_id} because task {dep_task.id} depends on it")

        return self.project_manager.delete_task(task_id)

    def list_tasks(
        self,
        story_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee: Optional[str] = None,
        include_completed: bool = True,
    ) -> List[Task]:
        """List tasks with optional filtering.

        Args:
            story_id: Filter by story ID
            status: Filter by status
            priority: Filter by priority
            assignee: Filter by assignee
            include_completed: Whether to include completed tasks

        Returns:
            List of tasks matching filters
        """
        tasks = self.project_manager.list_tasks()

        # Apply filters
        filtered_tasks = []
        for task in tasks:
            # Skip completed tasks if not requested
            if not include_completed and task.status == TaskStatus.DONE:
                continue

            # Apply filters
            if story_id and task.story_id != story_id:
                continue
            if status and task.status != status:
                continue
            if priority and task.priority != priority:
                continue
            if assignee and task.assignee != assignee:
                continue

            filtered_tasks.append(task)

        return filtered_tasks

    def get_tasks_by_story(self, story_id: str) -> List[Task]:
        """Get all tasks for a specific story.

        Args:
            story_id: Story ID

        Returns:
            List of tasks for the story
        """
        return self.list_tasks(story_id=story_id)

    def get_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """Get all tasks assigned to a specific person.

        Args:
            assignee: Person's identifier

        Returns:
            List of tasks assigned to the person
        """
        return self.list_tasks(assignee=assignee)

    def get_unassigned_tasks(self) -> List[Task]:
        """Get all unassigned tasks.

        Returns:
            List of unassigned tasks
        """
        tasks = self.project_manager.list_tasks()
        return [task for task in tasks if task.assignee is None]

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status.

        Args:
            status: Task status to filter by

        Returns:
            List of tasks with the specified status
        """
        return self.list_tasks(status=status)

    def assign_task(self, task_id: str, assignee: str) -> Optional[Task]:
        """Assign a task to someone.

        Args:
            task_id: Task ID
            assignee: Person to assign the task to

        Returns:
            Updated task if found, None otherwise
        """
        return self.update_task(task_id, assignee=assignee)

    def change_task_status(self, task_id: str, status: TaskStatus) -> Optional[Task]:
        """Change the status of a task.

        Args:
            task_id: Task ID
            status: New status

        Returns:
            Updated task if found, None otherwise
        """
        return self.update_task(task_id, status=status)

    def get_blocked_tasks(self) -> List[Task]:
        """Get all blocked tasks.

        Returns:
            List of blocked tasks
        """
        return self.list_tasks(status=TaskStatus.BLOCKED)

    def get_available_tasks(self, assignee: Optional[str] = None) -> List[Task]:
        """Get tasks that are available to be worked on (no blocking dependencies).

        Args:
            assignee: Optional assignee filter

        Returns:
            List of available tasks
        """
        all_tasks = self.list_tasks(assignee=assignee, include_completed=False)
        completed_task_ids = [t.id for t in self.list_tasks(status=TaskStatus.DONE)]

        available_tasks = []
        for task in all_tasks:
            if task.status == TaskStatus.TODO and task.can_start(completed_task_ids):
                available_tasks.append(task)

        return available_tasks

    def get_task_dependencies_info(self, task_id: str) -> Dict[str, Any]:
        """Get dependency information for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with dependency information
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        completed_task_ids = [t.id for t in self.list_tasks(status=TaskStatus.DONE)]

        dependencies_info = []
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if dep_task:
                dependencies_info.append(
                    {
                        "id": dep_id,
                        "title": dep_task.title,
                        "status": dep_task.status.value,
                        "completed": dep_task.status == TaskStatus.DONE,
                    }
                )

        return {
            "task_id": task_id,
            "task_title": task.title,
            "dependencies": dependencies_info,
            "can_start": task.can_start(completed_task_ids),
            "blocking_dependencies": [dep for dep in dependencies_info if not dep["completed"]],
        }

    def add_task_note(self, task_id: str, note: str) -> bool:
        """Add a note to a task.

        Args:
            task_id: Task ID
            note: Note content

        Returns:
            True if note was added, False if task not found
        """
        task = self.get_task(task_id)
        if not task:
            return False

        task.add_note(note)
        self.project_manager.save_task(task)

        return True

    def get_story_progress(self, story_id: str) -> Dict[str, Any]:
        """Get progress information for all tasks in a story.

        Args:
            story_id: Story ID

        Returns:
            Dictionary with progress information
        """
        tasks = self.get_tasks_by_story(story_id)

        if not tasks:
            return {
                "story_id": story_id,
                "total_tasks": 0,
                "progress_percentage": 0.0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "todo_tasks": 0,
                "blocked_tasks": 0,
            }

        completed = len([t for t in tasks if t.status == TaskStatus.DONE])
        in_progress = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        todo = len([t for t in tasks if t.status == TaskStatus.TODO])
        blocked = len([t for t in tasks if t.status == TaskStatus.BLOCKED])

        progress_percentage = (completed / len(tasks)) * 100 if tasks else 0

        return {
            "story_id": story_id,
            "total_tasks": len(tasks),
            "progress_percentage": progress_percentage,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "todo_tasks": todo,
            "blocked_tasks": blocked,
            "estimated_hours": sum(t.estimated_hours or 0 for t in tasks),
            "actual_hours": sum(t.actual_hours or 0 for t in tasks),
        }
