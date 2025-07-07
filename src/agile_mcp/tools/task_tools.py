"""Task management tools for Agile MCP Server."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import AgileTool, ToolError
from ..models.task import TaskStatus, TaskPriority


class CreateTaskTool(AgileTool):
    """Create a new task in the agile project."""
    
    def apply(self, title: str, description: str, story_id: Optional[str] = None, 
              priority: str = "medium", assignee: Optional[str] = None, 
              estimated_hours: Optional[float] = None, due_date: Optional[str] = None,
              dependencies: Optional[str] = None, tags: Optional[str] = None) -> str:
        """Create a new task.
        
        Args:
            title: Task title (required)
            description: Task description (required)
            story_id: ID of the parent story (optional)
            priority: Task priority (optional, default: medium)
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
        if estimated_hours is not None and estimated_hours < 0:
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
        task = self.agent.task_service.create_task(
            title=title,
            description=description,
            story_id=story_id,
            priority=priority_enum,
            assignee=assignee,
            estimated_hours=estimated_hours,
            due_date=due_date_obj,
            dependencies=dependencies_list,
            tags=tags_list
        )
        
        # Format result with task data
        task_data = task.model_dump(mode='json')
        self.last_result_data = task_data
        
        return f"Task '{task.title}' created successfully with ID {task.id}"


class GetTaskTool(AgileTool):
    """Retrieve a task by its ID."""
    
    def apply(self, task_id: str) -> str:
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
        task_data = task.model_dump(mode='json')
        self.last_result_data = task_data
        
        return f"Retrieved task: {task.title} (ID: {task.id})"


class UpdateTaskTool(AgileTool):
    """Update an existing task."""
    
    def apply(self, task_id: str, title: Optional[str] = None, description: Optional[str] = None,
              status: Optional[str] = None, priority: Optional[str] = None, 
              assignee: Optional[str] = None, estimated_hours: Optional[float] = None,
              actual_hours: Optional[float] = None, due_date: Optional[str] = None,
              dependencies: Optional[str] = None, tags: Optional[str] = None) -> str:
        """Update an existing task.
        
        Args:
            task_id: The ID of the task to update (required)
            title: New task title (optional)
            description: New task description (optional)
            status: New status (optional)
            priority: New priority (optional)
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
        if status is not None:
            try:
                TaskStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")
        
        # Validate priority if provided
        if priority is not None:
            try:
                TaskPriority(priority)
            except ValueError:
                valid_priorities = [p.value for p in TaskPriority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")
        
        # Validate hours if provided
        if estimated_hours is not None and estimated_hours < 0:
            raise ToolError("Estimated hours must be non-negative")
        if actual_hours is not None and actual_hours < 0:
            raise ToolError("Actual hours must be non-negative")
        
        # Prepare update parameters
        update_params = {}
        if title is not None:
            update_params["title"] = title
        if description is not None:
            update_params["description"] = description
        if status is not None:
            update_params["status"] = TaskStatus(status)
        if priority is not None:
            update_params["priority"] = TaskPriority(priority)
        if assignee is not None:
            update_params["assignee"] = assignee
        if estimated_hours is not None:
            update_params["estimated_hours"] = estimated_hours
        if actual_hours is not None:
            update_params["actual_hours"] = actual_hours
        if due_date is not None:
            try:
                update_params["due_date"] = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise ToolError("Due date must be in YYYY-MM-DD format")
        if dependencies is not None:
            update_params["dependencies"] = [dep.strip() for dep in dependencies.split(",")]
        if tags is not None:
            update_params["tags"] = [tag.strip() for tag in tags.split(",")]
        
        # Update the task
        updated_task = self.agent.task_service.update_task(task_id, **update_params)
        
        if updated_task is None:
            raise ToolError(f"Task with ID {task_id} not found")
        
        # Format result with task data
        task_data = updated_task.model_dump(mode='json')
        self.last_result_data = task_data
        
        return f"Task '{updated_task.title}' updated successfully"


class DeleteTaskTool(AgileTool):
    """Delete a task from the agile project."""
    
    def apply(self, task_id: str) -> str:
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
        deleted = self.agent.task_service.delete_task(task_id)
        
        if not deleted:
            raise ToolError(f"Failed to delete task with ID {task_id}")
        
        return f"Task '{task.title}' (ID: {task_id}) deleted successfully"


class ListTasksTool(AgileTool):
    """List tasks with optional filtering."""
    
    def apply(self, story_id: Optional[str] = None, status: Optional[str] = None,
              priority: Optional[str] = None, assignee: Optional[str] = None,
              include_completed: bool = True) -> str:
        """List tasks with optional filtering.
        
        Args:
            story_id: Filter by story ID (optional)
            status: Filter by status (optional)
            priority: Filter by priority (optional)
            assignee: Filter by assignee (optional)
            include_completed: Include completed tasks (optional, default: true)
            
        Returns:
            Success message with list of tasks
        """
        # Check if project is initialized
        self._check_project_initialized()
        
        # Validate filters
        if status is not None:
            try:
                TaskStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise ToolError(f"Invalid status. Must be one of: {valid_statuses}")
        
        if priority is not None:
            try:
                TaskPriority(priority)
            except ValueError:
                valid_priorities = [p.value for p in TaskPriority]
                raise ToolError(f"Invalid priority. Must be one of: {valid_priorities}")
        
        # Get filtered tasks
        tasks = self.agent.task_service.list_tasks(
            story_id=story_id,
            status=TaskStatus(status) if status else None,
            priority=TaskPriority(priority) if priority else None,
            assignee=assignee,
            include_completed=include_completed
        )
        
        # Format result
        tasks_data = [task.model_dump(mode='json') for task in tasks]
        self.last_result_data = {"tasks": tasks_data, "count": len(tasks)}
        
        if not tasks:
            return "No tasks found matching the specified criteria"
        
        task_summary = []
        for task in tasks:
            status_str = task.status.value
            assignee_str = f" (assigned to {task.assignee})" if task.assignee else ""
            story_str = f" [Story: {task.story_id}]" if task.story_id else ""
            task_summary.append(f"- {task.id}: {task.title} ({status_str}){assignee_str}{story_str}")
        
        return f"Found {len(tasks)} tasks:\n" + "\n".join(task_summary) 