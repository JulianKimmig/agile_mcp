"""Task model for Agile MCP Server."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from .base import AgileArtifact


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task(AgileArtifact):
    """Task model representing a subtask within a user story."""

    story_id: str | None = Field(default=None, description="ID of the parent story")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Task status")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    assignee: str | None = Field(default=None, description="Person assigned to this task")
    estimated_hours: float | None = Field(default=None, description="Estimated hours to complete")
    actual_hours: float | None = Field(default=None, description="Actual hours spent")
    due_date: datetime | None = Field(default=None, description="Task due date")
    tags: list[str] = Field(default_factory=list, description="Task tags")
    notes: list[str] = Field(default_factory=list, description="Task notes and updates")

    @model_validator(mode="before")
    @classmethod
    def migrate_dependencies(cls, data: Any) -> Any:
        """Migrate old list-based dependencies to new dict-based format."""
        if isinstance(data, dict) and "dependencies" in data:
            deps = data["dependencies"]
            if isinstance(deps, list):
                # This is the old format, migrate it.
                # Assuming old dependencies are always on other tasks.
                migrated_deps = {dep_id: "task" for dep_id in deps}
                data["dependencies"] = migrated_deps
        return data

    @field_validator("estimated_hours", "actual_hours")
    @classmethod
    def validate_hours(cls, v: float) -> float:
        """Validate that hours are non-negative."""
        if v and v < 0:
            raise ValueError("Hours must be non-negative")
        return v

    def add_note(self, note: str) -> None:
        """Add a note to the task.

        Args:
            note: Note content to add
        """
        timestamp = datetime.now().isoformat()
        self.notes.append(f"[{timestamp}] {note}")
        self.updated_at = datetime.now()

    def is_blocked(self) -> bool:
        """Check if task is blocked.

        Returns:
            True if task status is blocked
        """
        return self.status == TaskStatus.BLOCKED

    def is_completed(self) -> bool:
        """Check if task is completed.

        Returns:
            True if task status is done
        """
        return self.status == TaskStatus.DONE

    def get_progress_percentage(self) -> float:
        """Get task progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        if self.status == TaskStatus.DONE:
            return 100.0
        elif self.status == TaskStatus.IN_PROGRESS:
            return 50.0
        else:
            return 0.0
