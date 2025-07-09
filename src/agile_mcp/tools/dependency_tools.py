"""Dependency management tools for Agile MCP Server."""

from ..models.dependency import ArtifactType, DependencyType
from .base import AgileTool, ToolResult


class AddDependencyTool(AgileTool):
    """Tool for adding dependencies between artifacts."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters."""
        pass  # Validation handled by service

    def apply(
        self,
        artifact_id: str,
        artifact_type: str,
        depends_on_id: str,
        depends_on_type: str,
        dependency_type: str = "depends_on",
        description: str | None = None,
    ) -> ToolResult:
        """Add a dependency between two artifacts.

        Args:
            artifact_id: ID of the artifact that depends on another
            artifact_type: Type of the dependent artifact (epic/sprint/story/task)
            depends_on_id: ID of the artifact being depended upon
            depends_on_type: Type of the artifact being depended upon (epic/sprint/story/task)
            dependency_type: Type of dependency (depends_on/blocks/relates_to) (default: depends_on)
            description: Optional description of the dependency

        Returns:
            Success message with dependency details
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Convert string types to enums
            artifact_type_enum = ArtifactType(artifact_type.lower())
            depends_on_type_enum = ArtifactType(depends_on_type.lower())
            dependency_type_enum = DependencyType(dependency_type.lower())

            # Add the dependency
            success = self.agent.dependency_service.add_dependency(
                artifact_id=artifact_id,
                artifact_type=artifact_type_enum,
                depends_on_id=depends_on_id,
                depends_on_type=depends_on_type_enum,
                dependency_type=dependency_type_enum,
                description=description,
            )

            if success:
                return self.format_result(
                    f"Successfully added dependency: {artifact_type}:{artifact_id} {dependency_type} {depends_on_type}:{depends_on_id}",
                    {
                        "artifact_id": artifact_id,
                        "artifact_type": artifact_type,
                        "depends_on_id": depends_on_id,
                        "depends_on_type": depends_on_type,
                        "dependency_type": dependency_type,
                        "description": description,
                    },
                )
            else:
                return self.format_error("Failed to add dependency")

        except ValueError as e:
            return self.format_error(f"Invalid dependency: {str(e)}")
        except Exception as e:
            return self.format_error(f"Failed to add dependency: {str(e)}")


class RemoveDependencyTool(AgileTool):
    """Tool for removing dependencies between artifacts."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters."""
        pass

    def apply(self, artifact_id: str, artifact_type: str, depends_on_id: str) -> ToolResult:
        """Remove a dependency between two artifacts.

        Args:
            artifact_id: ID of the artifact that has the dependency
            artifact_type: Type of the artifact (epic/sprint/story/task)
            depends_on_id: ID of the dependency to remove

        Returns:
            Success message confirming removal
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Convert string type to enum
            artifact_type_enum = ArtifactType(artifact_type.lower())

            # Remove the dependency
            success = self.agent.dependency_service.remove_dependency(
                artifact_id=artifact_id, artifact_type=artifact_type_enum, depends_on_id=depends_on_id
            )

            if success:
                return self.format_result(
                    f"Successfully removed dependency from {artifact_type}:{artifact_id}",
                    {"artifact_id": artifact_id, "artifact_type": artifact_type, "removed_dependency": depends_on_id},
                )
            else:
                return self.format_error("Dependency not found")

        except Exception as e:
            return self.format_error(f"Failed to remove dependency: {str(e)}")


class GetDependenciesTool(AgileTool):
    """Tool for getting dependencies of an artifact."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters."""
        pass

    def apply(self, artifact_id: str, artifact_type: str) -> ToolResult:
        """Get all dependencies for an artifact.

        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of the artifact (epic/sprint/story/task)

        Returns:
            List of dependencies with their status
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Convert string type to enum
            artifact_type_enum = ArtifactType(artifact_type.lower())

            # Get dependencies
            dependencies = self.agent.dependency_service.get_dependencies(
                artifact_id=artifact_id, artifact_type=artifact_type_enum
            )

            # Format message
            if dependencies:
                dep_list = []
                for dep in dependencies:
                    status = "✅" if dep["is_completed"] else "⏳"
                    dep_list.append(f"{status} {dep['type']}:{dep['id']} - {dep['name']} ({dep['status']})")

                message = f"Dependencies for {artifact_type}:{artifact_id}:\n" + "\n".join(dep_list)
            else:
                message = f"No dependencies found for {artifact_type}:{artifact_id}"

            return self.format_result(
                message, {"artifact_id": artifact_id, "artifact_type": artifact_type, "dependencies": dependencies}
            )

        except Exception as e:
            return self.format_error(f"Failed to get dependencies: {str(e)}")


class CheckCanStartTool(AgileTool):
    """Tool for checking if an artifact can be started based on dependencies."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters."""
        pass

    def apply(self, artifact_id: str, artifact_type: str) -> ToolResult:
        """Check if an artifact can be started based on its dependencies.

        Args:
            artifact_id: ID of the artifact
            artifact_type: Type of the artifact (epic/sprint/story/task)

        Returns:
            Status indicating if artifact can be started and any blocking dependencies
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Convert string type to enum
            artifact_type_enum = ArtifactType(artifact_type.lower())

            # Check if can start
            result = self.agent.dependency_service.can_start_artifact(
                artifact_id=artifact_id, artifact_type=artifact_type_enum
            )

            # Format message
            if result.get("can_start"):
                message = f"✅ {artifact_type}:{artifact_id} can be started - all dependencies are completed"
            else:
                blocking = result.get("blocking_dependencies", [])
                if blocking:
                    block_list = []
                    for dep in blocking:
                        block_list.append(f"- {dep['type']}:{dep['id']} - {dep['name']} ({dep['status']})")
                    message = (
                        f"❌ {artifact_type}:{artifact_id} cannot be started due to incomplete dependencies:\n"
                        + "\n".join(block_list)
                    )
                else:
                    message = (
                        f"❌ {artifact_type}:{artifact_id} cannot be started: {result.get('reason', 'Unknown reason')}"
                    )

            return self.format_result(message, result)

        except Exception as e:
            return self.format_error(f"Failed to check dependencies: {str(e)}")


class GetDependencyGraphTool(AgileTool):
    """Tool for getting the complete dependency graph."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters."""
        pass

    def apply(self) -> ToolResult:
        """Get the complete dependency graph for the project.

        Returns:
            Dependency graph with all artifacts and their relationships
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Get dependency graph
            graph = self.agent.dependency_service.get_dependency_graph()

            # Count statistics
            total_nodes = len(graph["nodes"])
            total_edges = len(graph["edges"])
            completed_nodes = len([n for n in graph["nodes"] if n["is_completed"]])

            # Group by type
            by_type = {}
            for node in graph["nodes"]:
                node_type = node["type"]
                if node_type not in by_type:
                    by_type[node_type] = 0
                by_type[node_type] += 1

            # Format message
            message = f"""📊 Dependency Graph Summary:

Total Artifacts: {total_nodes}
Total Dependencies: {total_edges}
Completed: {completed_nodes}/{total_nodes}

By Type:"""
            for artifact_type, count in by_type.items():
                message += f"\n- {artifact_type.title()}s: {count}"

            if total_edges > 0:
                message += f"\n\n🔗 {total_edges} dependency relationships exist between artifacts"
            else:
                message += "\n\n🔗 No dependencies defined yet"

            return self.format_result(message, graph)

        except Exception as e:
            return self.format_error(f"Failed to get dependency graph: {str(e)}")
