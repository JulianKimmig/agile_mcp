"""Project overview tools for Agile MCP Server."""

from typing import Any, Dict, List

from .base import AgileTool, ToolResult


class GetProjectOverviewTool(AgileTool):
    """Tool for getting a comprehensive overview of all project artifacts."""

    def validate_input(self, input_data: dict) -> None:
        """Validate input parameters."""
        pass  # No parameters needed for this tool

    def apply(self, include_completed: bool = True, include_cancelled: bool = False) -> ToolResult:
        """Get a comprehensive overview of all project artifacts (epics, sprints, stories, and tasks).

        Args:
            include_completed: Include completed items in the overview (default: True)
            include_cancelled: Include cancelled items in the overview (default: False)

        Returns:
            Comprehensive project overview with all artifacts
        """
        # Check if project is initialized
        self._check_project_initialized()

        try:
            # Get all epics (include story IDs for relationships)
            epics = self.agent.epic_service.list_epics(include_story_ids=True)

            # Get all sprints (include story IDs for relationships)
            sprints = self.agent.sprint_service.list_sprints(include_story_ids=True)

            # Get all stories
            stories = self.agent.story_service.list_stories()

            # Get all tasks
            tasks = self.agent.task_service.list_tasks()

            # Filter items based on status if requested
            if not include_completed:
                epics = [epic for epic in epics if epic.status != "completed"]
                sprints = [sprint for sprint in sprints if sprint.status != "completed"]
                stories = [story for story in stories if story.status != "done"]
                tasks = [task for task in tasks if task.status != "done"]

            if not include_cancelled:
                epics = [epic for epic in epics if epic.status != "cancelled"]
                sprints = [sprint for sprint in sprints if sprint.status != "cancelled"]
                # Stories don't have cancelled status, they use 'done' or other statuses
                tasks = [task for task in tasks if task.status != "blocked"]  # Using blocked as closest to cancelled

            # Build comprehensive overview
            overview_data = {
                "project_path": str(self.agent.project_path),
                "summary": {
                    "total_epics": len(epics),
                    "total_sprints": len(sprints),
                    "total_stories": len(stories),
                    "total_tasks": len(tasks),
                },
                "epics": [],
                "sprints": [],
                "stories": [],
                "tasks": [],
                "relationships": {
                    "epic_stories": {},  # epic_id -> [story_ids]
                    "sprint_stories": {},  # sprint_id -> [story_ids]
                    "story_tasks": {},  # story_id -> [task_ids]
                },
            }

            # Process epics
            for epic in epics:
                epic_data = {
                    "id": epic.id,
                    "name": epic.name,
                    "description": epic.description,
                    "status": epic.status,
                    "tags": epic.tags,
                    "story_ids": epic.story_ids,
                    "dependencies": epic.dependencies,
                    "created_at": epic.created_at.isoformat(),
                    "updated_at": epic.updated_at.isoformat(),
                }
                overview_data["epics"].append(epic_data)
                overview_data["relationships"]["epic_stories"][epic.id] = epic.story_ids

            # Process sprints
            for sprint in sprints:
                sprint_data = {
                    "id": sprint.id,
                    "name": sprint.name,
                    "goal": sprint.goal,
                    "status": sprint.status,
                    "start_date": sprint.start_date.isoformat() if sprint.start_date else None,
                    "end_date": sprint.end_date.isoformat() if sprint.end_date else None,
                    "tags": sprint.tags,
                    "story_ids": sprint.story_ids,
                    "dependencies": sprint.dependencies,
                    "created_at": sprint.created_at.isoformat(),
                    "updated_at": sprint.updated_at.isoformat(),
                }
                overview_data["sprints"].append(sprint_data)
                overview_data["relationships"]["sprint_stories"][sprint.id] = sprint.story_ids

            # Process stories
            for story in stories:
                # Find epic_id by looking through epics that contain this story
                epic_id = None
                for epic in epics:
                    if story.id in epic.story_ids:
                        epic_id = epic.id
                        break

                story_data = {
                    "id": story.id,
                    "name": story.name,
                    "description": story.description,
                    "status": story.status,
                    "priority": story.priority,
                    "points": story.points,
                    "tags": story.tags,
                    "epic_id": epic_id,
                    "sprint_id": story.sprint_id,
                    "dependencies": story.dependencies,
                    "created_at": story.created_at.isoformat(),
                    "updated_at": story.updated_at.isoformat(),
                }
                overview_data["stories"].append(story_data)

                # Build story->tasks relationship
                story_tasks = [task for task in tasks if task.story_id == story.id]
                overview_data["relationships"]["story_tasks"][story.id] = [task.id for task in story_tasks]

            # Process tasks
            for task in tasks:
                task_data = {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "assignee": task.assignee,
                    "story_id": task.story_id,
                    "estimated_hours": task.estimated_hours,
                    "actual_hours": task.actual_hours,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "dependencies": task.dependencies,
                    "tags": task.tags,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                overview_data["tasks"].append(task_data)

            # Add status breakdown for summary
            overview_data["summary"]["status_breakdown"] = {
                "epics": self._get_status_breakdown([epic.status for epic in epics]),
                "sprints": self._get_status_breakdown([sprint.status for sprint in sprints]),
                "stories": self._get_status_breakdown([story.status for story in stories]),
                "tasks": self._get_status_breakdown([task.status for task in tasks]),
            }

            # Add priority breakdown for stories and tasks
            overview_data["summary"]["priority_breakdown"] = {
                "stories": self._get_priority_breakdown([story.priority for story in stories]),
                "tasks": self._get_priority_breakdown([task.priority for task in tasks]),
            }

            # Create comprehensive message
            message = self._format_overview_message(overview_data)

            return self.format_result(message, overview_data)

        except Exception as e:
            raise e
            return self.format_error(f"Failed to get project overview: {str(e)}")

    def _get_status_breakdown(self, statuses: List[str]) -> Dict[str, int]:
        """Get a breakdown of statuses.

        Args:
            statuses: List of status strings

        Returns:
            Dictionary with status counts
        """
        breakdown = {}
        for status in statuses:
            breakdown[status] = breakdown.get(status, 0) + 1
        return breakdown

    def _get_priority_breakdown(self, priorities: List[str]) -> Dict[str, int]:
        """Get a breakdown of priorities.

        Args:
            priorities: List of priority strings

        Returns:
            Dictionary with priority counts
        """
        breakdown = {}
        for priority in priorities:
            breakdown[priority] = breakdown.get(priority, 0) + 1
        return breakdown

    def _format_overview_message(self, overview_data: Dict[str, Any]) -> str:
        """Format a comprehensive overview message.

        Args:
            overview_data: The overview data dictionary

        Returns:
            Formatted message string
        """
        summary = overview_data["summary"]

        message = f"""📋 Project Overview: {overview_data["project_path"]}

📊 Summary:
• Epics: {summary["total_epics"]}
• Sprints: {summary["total_sprints"]}
• Stories: {summary["total_stories"]}
• Tasks: {summary["total_tasks"]}

📈 Status Breakdown:
"""

        # Add status breakdowns
        for artifact_type, breakdown in summary["status_breakdown"].items():
            if breakdown:
                status_list = [f"{status}: {count}" for status, count in breakdown.items()]
                message += f"• {artifact_type.title()}: {', '.join(status_list)}\n"

        # Add priority breakdowns
        if summary.get("priority_breakdown"):
            message += "\n🎯 Priority Breakdown:\n"
            for artifact_type, breakdown in summary["priority_breakdown"].items():
                if breakdown:
                    priority_list = [f"{priority}: {count}" for priority, count in breakdown.items()]
                    message += f"• {artifact_type.title()}: {', '.join(priority_list)}\n"

        # Add relationship info
        relationships = overview_data["relationships"]
        epics_with_stories = len([epic_id for epic_id, story_ids in relationships["epic_stories"].items() if story_ids])
        sprints_with_stories = len(
            [sprint_id for sprint_id, story_ids in relationships["sprint_stories"].items() if story_ids]
        )
        stories_with_tasks = len([story_id for story_id, task_ids in relationships["story_tasks"].items() if task_ids])

        message += f"""
🔗 Relationships:
• Epics with stories: {epics_with_stories}/{summary["total_epics"]}
• Sprints with stories: {sprints_with_stories}/{summary["total_sprints"]}
• Stories with tasks: {stories_with_tasks}/{summary["total_stories"]}

Use the 'data' field for detailed information about all artifacts and their relationships."""

        return message
