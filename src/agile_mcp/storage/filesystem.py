"""Filesystem storage layer for agile project management."""

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type, cast

import yaml

if TYPE_CHECKING:
    from ..models.base import AgileArtifact
    from ..models.sprint import Sprint
    from ..models.story import UserStory
    from ..models.task import Task
from ..models.epic import Epic


class AgileProjectManager:
    """Manages the .agile directory structure and project initialization."""

    def __init__(self, project_path: str | Path):
        """Initialize the project manager.

        Args:
            project_path: Path to the project directory

        Raises:
            ValueError: If project path doesn't exist or is not a directory
        """
        self.project_path = Path(project_path)

        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        if not self.project_path.is_dir():
            raise ValueError(f"Project path must be a directory: {project_path}")

        self.agile_dir = self.project_path / ".agile"

    def initialize(self) -> None:
        """Initialize the .agile directory structure if it doesn't exist."""
        if self.is_initialized():
            return  # Already initialized, do nothing

        # Create main .agile directory
        self.agile_dir.mkdir(exist_ok=True)

        # Create subdirectories
        subdirs = ["stories", "sprints", "tasks", "epics", "reports", "archive"]
        for subdir in subdirs:
            subdir_path = self.agile_dir / subdir
            self._ensure_directory(subdir_path)

        # Create default config file
        self._create_default_config()

    def is_initialized(self) -> bool:
        """Check if the project is already initialized with .agile structure.

        Returns:
            True if initialized, False otherwise
        """
        return self.agile_dir.exists() and self.agile_dir.is_dir()

    def get_agile_dir(self) -> Path:
        """Get the path to the .agile directory.

        Returns:
            Path to the .agile directory
        """
        return self.agile_dir

    def get_stories_dir(self) -> Path:
        """Get the path to the stories directory."""
        return self.agile_dir / "stories"

    def get_sprints_dir(self) -> Path:
        """Get the path to the sprints directory."""
        return self.agile_dir / "sprints"

    def get_tasks_dir(self) -> Path:
        """Get the path to the tasks directory."""
        return self.agile_dir / "tasks"

    def get_epics_dir(self) -> Path:
        """Get the path to the epics directory."""
        return self.agile_dir / "epics"

    def get_reports_dir(self) -> Path:
        """Get the path to the reports directory."""
        return self.agile_dir / "reports"

    def get_archive_dir(self) -> Path:
        """Get the path to the archive directory."""
        return self.agile_dir / "archive"

    def _ensure_directory(self, path: Path) -> None:
        """Ensure a directory exists, creating it if necessary.

        Args:
            path: Path to the directory to create
        """
        path.mkdir(parents=True, exist_ok=True)

    def _create_default_config(self) -> None:
        """Create a default config.yml file."""
        config = {
            "project": {"name": self.project_path.name, "version": "1.0.0", "created_at": "auto-generated"},
            "agile": {"methodology": "scrum", "story_point_scale": [1, 2, 3, 5, 8, 13, 21], "sprint_duration_weeks": 2},
        }

        config_path = self.agile_dir / "config.yml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def create_backup(self) -> Path:
        """Create a backup of the entire .agile directory.

        Returns:
            Path to the created backup file
        """
        backup_dir = tempfile.mkdtemp()
        backup_name = f"agile_backup_{self.project_path.name}"
        backup_path = Path(backup_dir) / f"{backup_name}.tar.gz"

        # Create tar.gz backup
        shutil.make_archive(
            str(backup_path).replace(".tar.gz", ""), "gztar", root_dir=str(self.agile_dir.parent), base_dir=".agile"
        )

        return backup_path

    def restore_backup(self, backup_path: Path) -> None:
        """Restore from a backup file.

        Args:
            backup_path: Path to the backup file to restore
        """
        if not backup_path.exists():
            raise ValueError(f"Backup file does not exist: {backup_path}")

        # Remove current .agile directory if it exists
        if self.agile_dir.exists():
            shutil.rmtree(self.agile_dir)

        # Extract backup
        shutil.unpack_archive(str(backup_path), extract_dir=str(self.project_path))

    # Story management methods
    def save_story(self, story: "UserStory") -> None:
        """Save a story to filesystem in status-based subfolder.

        Args:
            story: Story instance to save
        """
        # Get the correct file path based on status
        story_file = self._get_artifact_file_path(self.get_stories_dir(), story.id, story.status.value)
        story_data = story.model_dump(mode="json")

        # Check if the story exists elsewhere and migrate it first
        existing_file = self._find_artifact_file(self.get_stories_dir(), story.id)
        if existing_file and existing_file != story_file:
            # Remove the old file as we're saving to the new location
            existing_file.unlink()

        with open(story_file, "w", encoding="utf-8") as f:
            yaml.dump(story_data, f, default_flow_style=False, sort_keys=False)

    def get_story(self, story_id: str) -> Optional["UserStory"]:
        """Get a story by ID from any status folder.

        Args:
            story_id: Story ID

        Returns:
            UserStory instance if found, None otherwise
        """
        from ..models.story import UserStory

        story_file = self._find_artifact_file(self.get_stories_dir(), story_id)

        if not story_file:
            return None

        return cast(Optional["UserStory"], self._load_and_verify_artifact(story_file, UserStory))

    def delete_story(self, story_id: str) -> bool:
        """Delete a story by ID from any status folder.

        Args:
            story_id: Story ID

        Returns:
            True if story was deleted, False if not found
        """
        story_file = self._find_artifact_file(self.get_stories_dir(), story_id)

        if not story_file:
            return False

        try:
            story_file.unlink()
            return True
        except Exception:
            return False

    def list_stories(self) -> list["UserStory"]:
        """List all stories from all status folders.

        Returns:
            List of all story instances
        """
        from ..models.story import UserStory

        stories: list[UserStory] = []
        stories_dir = self.get_stories_dir()

        # Get files from status subfolders
        for status_dir in stories_dir.iterdir():
            if status_dir.is_dir():
                story_files = list(status_dir.glob("*.yml"))
                for story_file in story_files:
                    story = self._load_and_verify_artifact(story_file, UserStory)
                    if story:
                        stories.append(cast(UserStory, story))

        # Also check root directory for backwards compatibility
        root_story_files = list(stories_dir.glob("*.yml"))
        for story_file in root_story_files:
            story = self._load_and_verify_artifact(story_file, UserStory)
            if story:
                stories.append(cast(UserStory, story))

        return stories

    # Sprint management methods
    def save_sprint(self, sprint: "Sprint") -> None:
        """Save a sprint to filesystem in status-based subfolder.

        Args:
            sprint: Sprint instance to save
        """
        # Get the correct file path based on status
        sprint_file = self._get_artifact_file_path(self.get_sprints_dir(), sprint.id, sprint.status.value)
        sprint_data = sprint.model_dump(mode="json")

        # Check if the sprint exists elsewhere and migrate it first
        existing_file = self._find_artifact_file(self.get_sprints_dir(), sprint.id)
        if existing_file and existing_file != sprint_file:
            # Remove the old file as we're saving to the new location
            existing_file.unlink()

        with open(sprint_file, "w", encoding="utf-8") as f:
            yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False)

    def get_sprint(self, sprint_id: str) -> Optional["Sprint"]:
        """Get a sprint by ID from any status folder.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint instance if found, None otherwise
        """
        from ..models.sprint import Sprint

        sprint_file = self._find_artifact_file(self.get_sprints_dir(), sprint_id)

        if not sprint_file:
            return None

        return cast(Optional["Sprint"], self._load_and_verify_artifact(sprint_file, Sprint))

    def delete_sprint(self, sprint_id: str) -> bool:
        """Delete a sprint by ID from any status folder.

        Args:
            sprint_id: Sprint ID

        Returns:
            True if sprint was deleted, False if not found
        """
        sprint_file = self._find_artifact_file(self.get_sprints_dir(), sprint_id)

        if not sprint_file:
            return False

        try:
            sprint_file.unlink()
            return True
        except Exception:
            return False

    def list_sprints(self) -> list["Sprint"]:
        """List all sprints from all status folders.

        Returns:
            List of all sprint instances
        """
        from ..models.sprint import Sprint

        sprints: list[Sprint] = []
        sprints_dir = self.get_sprints_dir()

        # Get files from status subfolders
        for status_dir in sprints_dir.iterdir():
            if status_dir.is_dir():
                sprint_files = list(status_dir.glob("*.yml"))
                for sprint_file in sprint_files:
                    sprint = self._load_and_verify_artifact(sprint_file, Sprint)
                    if sprint:
                        sprints.append(cast(Sprint, sprint))

        # Also check root directory for backwards compatibility
        root_sprint_files = list(sprints_dir.glob("*.yml"))
        for sprint_file in root_sprint_files:
            sprint = self._load_and_verify_artifact(sprint_file, Sprint)
            if sprint:
                sprints.append(cast(Sprint, sprint))

        return sprints

    # Task management methods
    def save_task(self, task: "Task") -> None:
        """Save a task to filesystem in status-based subfolder.

        Args:
            task: Task instance to save
        """
        # Get the correct file path based on status
        task_file = self._get_artifact_file_path(self.get_tasks_dir(), task.id, task.status.value)
        task_data = task.model_dump(mode="json")

        # Check if the task exists elsewhere and migrate it first
        existing_file = self._find_artifact_file(self.get_tasks_dir(), task.id)
        if existing_file and existing_file != task_file:
            # Remove the old file as we're saving to the new location
            existing_file.unlink()

        with open(task_file, "w", encoding="utf-8") as f:
            yaml.dump(task_data, f, default_flow_style=False, sort_keys=False)

    def get_task(self, task_id: str) -> Optional["Task"]:
        """Get a task by ID from any status folder.

        Args:
            task_id: Task ID

        Returns:
            Task instance if found, None otherwise
        """
        from ..models.task import Task

        task_file = self._find_artifact_file(self.get_tasks_dir(), task_id)

        if not task_file:
            return None

        return cast(Optional["Task"], self._load_and_verify_artifact(task_file, Task))

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID from any status folder.

        Args:
            task_id: Task ID

        Returns:
            True if task was deleted, False if not found
        """
        task_file = self._find_artifact_file(self.get_tasks_dir(), task_id)

        if not task_file:
            return False

        try:
            task_file.unlink()
            return True
        except Exception:
            return False

    def list_tasks(self) -> list["Task"]:
        """List all tasks from all status folders.

        Returns:
            List of all task instances
        """
        from ..models.task import Task

        tasks: list[Task] = []
        tasks_dir = self.get_tasks_dir()

        # Get files from status subfolders
        for status_dir in tasks_dir.iterdir():
            if status_dir.is_dir():
                task_files = list(status_dir.glob("*.yml"))
                for task_file in task_files:
                    task = self._load_and_verify_artifact(task_file, Task)
                    if task:
                        tasks.append(cast(Task, task))

        # Also check root directory for backwards compatibility
        root_task_files = list(tasks_dir.glob("*.yml"))
        for task_file in root_task_files:
            task = self._load_and_verify_artifact(task_file, Task)
            if task:
                tasks.append(cast(Task, task))

        return tasks

    # Epic management methods
    def save_epic(self, epic: "Epic") -> None:
        """Save an epic to filesystem in status-based subfolder.

        Args:
            epic: Epic instance to save
        """
        # Get the correct file path based on status
        epic_file = self._get_artifact_file_path(self.get_epics_dir(), epic.id, epic.status.value)
        epic_data = epic.model_dump(mode="json")

        # Check if the epic exists elsewhere and migrate it first
        existing_file = self._find_artifact_file(self.get_epics_dir(), epic.id)
        if existing_file and existing_file != epic_file:
            # Remove the old file as we're saving to the new location
            existing_file.unlink()

        with open(epic_file, "w", encoding="utf-8") as f:
            yaml.dump(epic_data, f, default_flow_style=False, sort_keys=False)

    def get_epic(self, epic_id: str) -> Optional["Epic"]:
        """Get an epic by ID from any status folder.

        Args:
            epic_id: Epic ID

        Returns:
            Epic instance if found, None otherwise
        """
        from ..models.epic import Epic

        epic_file = self._find_artifact_file(self.get_epics_dir(), epic_id)

        if not epic_file:
            return None

        return cast(Optional["Epic"], self._load_and_verify_artifact(epic_file, Epic))

    def delete_epic(self, epic_id: str) -> bool:
        """Delete an epic by ID from any status folder.

        Args:
            epic_id: Epic ID

        Returns:
            True if epic was deleted, False if not found
        """
        epic_file = self._find_artifact_file(self.get_epics_dir(), epic_id)

        if not epic_file:
            return False

        try:
            epic_file.unlink()
            return True
        except Exception:
            return False

    def list_epics(self) -> list["Epic"]:
        """List all epics from all status folders.

        Returns:
            List of all epic instances
        """
        from ..models.epic import Epic

        epics: list[Epic] = []
        epics_dir = self.get_epics_dir()

        # Get files from status subfolders
        for status_dir in epics_dir.iterdir():
            if status_dir.is_dir():
                epic_files = list(status_dir.glob("*.yml"))
                for epic_file in epic_files:
                    epic = self._load_and_verify_artifact(epic_file, Epic)
                    if epic:
                        epics.append(cast(Epic, epic))

        # Also check root directory for backwards compatibility
        root_epic_files = list(epics_dir.glob("*.yml"))
        for epic_file in root_epic_files:
            epic = self._load_and_verify_artifact(epic_file, Epic)
            if epic:
                epics.append(cast(Epic, epic))

        return epics

    def _get_status_subfolder_path(self, base_dir: Path, status: str) -> Path:
        """Get the path to a status-based subfolder under the type directory.

        Args:
            base_dir: The base directory (stories, sprints, tasks)
            status: The status value

        Returns:
            Path to the status subfolder (e.g. stories/done/)
        """
        status_dir = base_dir / status
        self._ensure_directory(status_dir)
        return status_dir

    def _get_artifact_file_path(self, base_dir: Path, artifact_id: str, status: str) -> Path:
        """Get the file path for an artifact based on its status.

        Args:
            base_dir: The base directory (stories, sprints, tasks)
            artifact_id: The artifact ID
            status: The artifact status

        Returns:
            Path to the artifact file
        """
        status_dir = self._get_status_subfolder_path(base_dir, status)
        return status_dir / f"{artifact_id}.yml"

    def _find_artifact_file(self, base_dir: Path, artifact_id: str) -> Path | None:
        """Find an artifact file, checking both status subfolders and root directory of the type.

        Args:
            base_dir: The base directory (stories, sprints, tasks)
            artifact_id: The artifact ID to find

        Returns:
            Path to the artifact file if found, None otherwise
        """
        filename = f"{artifact_id}.yml"
        # Check status subfolders under the type directory
        for status_dir in base_dir.iterdir():
            if status_dir.is_dir():
                file_path = status_dir / filename
                if file_path.exists():
                    return file_path
        # Then check root of the type directory for backwards compatibility
        root_file = base_dir / filename
        if root_file.exists():
            return root_file
        return None

    def _migrate_artifact_to_status_folder(self, artifact: "AgileArtifact", base_dir: Path) -> None:
        """Migrate an artifact file to the correct status folder under the type directory.

        Args:
            artifact: The artifact instance
            base_dir: The base directory (stories, sprints, tasks)
        """
        current_file = self._find_artifact_file(base_dir, artifact.id)
        if not current_file:
            return
        # Get the correct path based on status
        if hasattr(artifact, "status"):
            correct_path = self._get_artifact_file_path(base_dir, artifact.id, artifact.status.value)
            # Only move if the file is not already in the correct location
            if current_file != correct_path:
                correct_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(current_file), str(correct_path))

    def _load_and_verify_artifact(
        self, file_path: Path, artifact_class: Type["AgileArtifact"]
    ) -> Optional["AgileArtifact"]:
        """Load an artifact and verify its status matches the  location.

        Args:
            file_path: Path to the artifact file
            artifact_class: The artifact class to instantiate

        Returns:
            Artifact instance if loaded successfully, None otherwise
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                artifact_data = yaml.safe_load(f)
            if not isinstance(artifact_data, dict):
                return None
            artifact = artifact_class(**artifact_data)
            # Check if the file is in the correct status folder under the type directory
            if hasattr(artifact, "status"):
                expected_status = artifact.status.value
                parent_folder = file_path.parent.name
                base_dir = file_path.parent.parent
                if parent_folder != expected_status:
                    self._migrate_artifact_to_status_folder(artifact, base_dir)
            return artifact
        except Exception as e:
            print(f"Error loading artifact from {file_path}: {e}")
            return None

    def clean_story_references(self, story_ids: list[str], artifact_type: str, artifact_id: str) -> list[str]:
        """Clean broken story references from a list of story IDs.

        This utility method checks which stories actually exist and logs warnings
        for any broken references found.

        Args:
            story_ids: List of story IDs to validate
            artifact_type: Type of artifact being cleaned (e.g., "Sprint", "Epic") for logging
            artifact_id: ID of the artifact being cleaned for logging

        Returns:
            List of valid story IDs (subset of input list)
        """
        if not story_ids:
            return []

        valid_story_ids = []
        broken_story_ids = []

        for story_id in story_ids:
            story = self.get_story(story_id)
            if story:
                valid_story_ids.append(story_id)
            else:
                broken_story_ids.append(story_id)

        # Log warning if broken references were found
        if broken_story_ids:
            import sys

            print(
                f"Warning: {artifact_type} {artifact_id} contains broken story references: {broken_story_ids}",
                file=sys.stderr,
            )

        return valid_story_ids
