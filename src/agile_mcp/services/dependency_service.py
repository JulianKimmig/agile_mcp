"""Service for managing cross-artifact dependencies."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.dependency import ArtifactType, DependencyType
from ..models.epic import EpicStatus
from ..models.sprint import SprintStatus
from ..models.story import StoryStatus
from ..models.task import TaskStatus
from ..storage.filesystem import AgileProjectManager


class DependencyService:
    """Service for managing dependencies between artifacts."""

    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the dependency service.

        Args:
            project_manager: The project manager for file operations
        """
        self.project_manager = project_manager

    def add_dependency(
        self,
        artifact_id: str,
        artifact_type: ArtifactType,
        depends_on_id: str,
        depends_on_type: ArtifactType,
        dependency_type: DependencyType = DependencyType.DEPENDS_ON,
        description: Optional[str] = None,
    ) -> bool:
        """Add a dependency between two artifacts.

        Args:
            artifact_id: ID of the artifact that depends on another
            artifact_type: Type of the dependent artifact
            depends_on_id: ID of the artifact being depended upon
            depends_on_type: Type of the artifact being depended upon
            dependency_type: Type of dependency (default: DEPENDS_ON)
            description: Optional description of the dependency

        Returns:
            True if dependency was added successfully

        Raises:
            ValueError: If artifacts don't exist or circular dependency detected
        """
        # Validate artifacts exist
        if not self._artifact_exists(artifact_id, artifact_type):
            raise ValueError(f"{artifact_type} with ID {artifact_id} not found")
        if not self._artifact_exists(depends_on_id, depends_on_type):
            raise ValueError(f"{depends_on_type} with ID {depends_on_id} not found")

        # Check for circular dependencies
        if self._would_create_circular_dependency(artifact_id, artifact_type, depends_on_id, depends_on_type):
            raise ValueError("Adding this dependency would create a circular dependency")

        # Get the artifact and update its dependencies
        artifact = self._get_artifact(artifact_id, artifact_type)
        if artifact:
            artifact.dependencies[depends_on_id] = depends_on_type.value
            artifact.updated_at = datetime.now()
            self._save_artifact(artifact, artifact_type)
            return True

        return False

    def remove_dependency(self, artifact_id: str, artifact_type: ArtifactType, depends_on_id: str) -> bool:
        """Remove a dependency between two artifacts.

        Args:
            artifact_id: ID of the artifact that has the dependency
            artifact_type: Type of the artifact
            depends_on_id: ID of the dependency to remove

        Returns:
            True if dependency was removed successfully
        """
        artifact = self._get_artifact(artifact_id, artifact_type)
        if artifact and depends_on_id in artifact.dependencies:
            del artifact.dependencies[depends_on_id]
            artifact.updated_at = datetime.now()
            self._save_artifact(artifact, artifact_type)
            return True
        return False

    def get_dependencies(self, artifact_id: str, artifact_type: ArtifactType) -> List[Dict[str, Any]]:
        """Get all dependencies for an artifact.

        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of the artifact

        Returns:
            List of dependency information
        """
        artifact = self._get_artifact(artifact_id, artifact_type)
        if not artifact:
            return []

        dependencies = []
        for dep_id, dep_type in artifact.dependencies.items():
            dep_artifact = self._get_artifact(dep_id, ArtifactType(dep_type))
            if dep_artifact:
                dependencies.append(
                    {
                        "id": dep_id,
                        "type": dep_type,
                        "name": getattr(dep_artifact, "name", getattr(dep_artifact, "name", "Unknown")),
                        "status": self._get_artifact_status(dep_artifact, ArtifactType(dep_type)),
                        "is_completed": self._is_artifact_completed(dep_artifact, ArtifactType(dep_type)),
                    }
                )

        return dependencies

    def can_start_artifact(self, artifact_id: str, artifact_type: ArtifactType) -> Dict[str, Any]:
        """Check if an artifact can be started based on its dependencies.

        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of the artifact

        Returns:
            Dictionary with can_start boolean and blocking dependencies
        """
        artifact = self._get_artifact(artifact_id, artifact_type)
        if not artifact:
            return {"can_start": False, "reason": "Artifact not found"}

        blocking_dependencies = []
        for dep_id, dep_type in artifact.dependencies.items():
            dep_artifact = self._get_artifact(dep_id, ArtifactType(dep_type))
            if dep_artifact and not self._is_artifact_completed(dep_artifact, ArtifactType(dep_type)):
                blocking_dependencies.append(
                    {
                        "id": dep_id,
                        "type": dep_type,
                        "name": getattr(dep_artifact, "name", getattr(dep_artifact, "name", "Unknown")),
                        "status": self._get_artifact_status(dep_artifact, ArtifactType(dep_type)),
                    }
                )

        return {"can_start": len(blocking_dependencies) == 0, "blocking_dependencies": blocking_dependencies}

    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get the complete dependency graph for the project.

        Returns:
            Dictionary representing the dependency graph
        """
        graph = {"nodes": [], "edges": []}

        # Add all artifacts as nodes
        for artifact_type in ArtifactType:
            artifacts = self._get_all_artifacts_of_type(artifact_type)
            for artifact in artifacts:
                graph["nodes"].append(
                    {
                        "id": artifact.id,
                        "type": artifact_type.value,
                        "name": getattr(artifact, "name", getattr(artifact, "name", "Unknown")),
                        "status": self._get_artifact_status(artifact, artifact_type),
                        "is_completed": self._is_artifact_completed(artifact, artifact_type),
                    }
                )

                # Add edges for dependencies
                for dep_id, dep_type in artifact.dependencies.items():
                    graph["edges"].append({"from": dep_id, "to": artifact.id, "type": "depends_on"})

        return graph

    def _artifact_exists(self, artifact_id: str, artifact_type: ArtifactType) -> bool:
        """Check if an artifact exists."""
        return self._get_artifact(artifact_id, artifact_type) is not None

    def _get_artifact(self, artifact_id: str, artifact_type: ArtifactType) -> Any:
        """Get an artifact by ID and type."""
        if artifact_type == ArtifactType.EPIC:
            return self.project_manager.get_epic(artifact_id)
        elif artifact_type == ArtifactType.SPRINT:
            return self.project_manager.get_sprint(artifact_id)
        elif artifact_type == ArtifactType.STORY:
            return self.project_manager.get_story(artifact_id)
        elif artifact_type == ArtifactType.TASK:
            return self.project_manager.get_task(artifact_id)
        return None

    def _save_artifact(self, artifact: Any, artifact_type: ArtifactType) -> None:
        """Save an artifact."""
        if artifact_type == ArtifactType.EPIC:
            self.project_manager.save_epic(artifact)
        elif artifact_type == ArtifactType.SPRINT:
            self.project_manager.save_sprint(artifact)
        elif artifact_type == ArtifactType.STORY:
            self.project_manager.save_story(artifact)
        elif artifact_type == ArtifactType.TASK:
            self.project_manager.save_task(artifact)

    def _get_all_artifacts_of_type(self, artifact_type: ArtifactType) -> List[Any]:
        """Get all artifacts of a specific type."""
        if artifact_type == ArtifactType.EPIC:
            return self.project_manager.list_epics()
        elif artifact_type == ArtifactType.SPRINT:
            return self.project_manager.list_sprints()
        elif artifact_type == ArtifactType.STORY:
            return self.project_manager.list_stories()
        elif artifact_type == ArtifactType.TASK:
            return self.project_manager.list_tasks()
        return []

    def _is_artifact_completed(self, artifact: Any, artifact_type: ArtifactType) -> bool:
        """Check if an artifact is completed."""
        if artifact_type == ArtifactType.EPIC:
            return artifact.status == EpicStatus.COMPLETED
        elif artifact_type == ArtifactType.SPRINT:
            return artifact.status == SprintStatus.COMPLETED
        elif artifact_type == ArtifactType.STORY:
            return artifact.status == StoryStatus.DONE
        elif artifact_type == ArtifactType.TASK:
            return artifact.status == TaskStatus.DONE
        return False

    def _get_artifact_status(self, artifact: Any, artifact_type: ArtifactType) -> str:
        """Get the status of an artifact."""
        return str(artifact.status.value if hasattr(artifact.status, "value") else artifact.status)

    def _would_create_circular_dependency(
        self, artifact_id: str, artifact_type: ArtifactType, depends_on_id: str, depends_on_type: ArtifactType
    ) -> bool:
        """Check if adding a dependency would create a circular dependency.

        Uses depth-first search to detect cycles.
        """
        visited = set()

        def has_path(from_id: str, from_type: ArtifactType, to_id: str) -> bool:
            """Check if there's a path from from_id to to_id through dependencies."""
            if from_id == to_id:
                return True

            if from_id in visited:
                return False

            visited.add(from_id)

            artifact = self._get_artifact(from_id, from_type)
            if artifact:
                for dep_id, dep_type_str in artifact.dependencies.items():
                    if has_path(dep_id, ArtifactType(dep_type_str), to_id):
                        return True

            return False

        # Check if depends_on_id can reach artifact_id through dependencies
        return has_path(depends_on_id, depends_on_type, artifact_id)
