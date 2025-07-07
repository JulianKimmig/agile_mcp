"""Project Status Service for aggregating status information from all services."""

from datetime import datetime
from typing import Dict, List, Any, Optional

from ..storage.filesystem import AgileProjectManager
from .config_service import ConfigurationService
from .story_service import StoryService
from .sprint_service import SprintService
from .task_service import TaskService
from .epic_service import EpicService


class ProjectStatusService:
    """Service for aggregating project status information from all services."""
    
    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the service with project manager."""
        self.project_manager = project_manager
        self.config_service = ConfigurationService(project_manager)
        self.story_service = StoryService(project_manager)
        self.sprint_service = SprintService(project_manager)
        self.task_service = TaskService(project_manager)
        self.epic_service = EpicService(project_manager)
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get comprehensive project status summary.
        
        Returns:
            Dictionary containing all project status information including:
            - project_config: Project configuration details
            - agile_config: Agile methodology configuration
            - stories: Story statistics and counts
            - tasks: Task statistics and counts
            - epics: Epic statistics and counts
            - sprints: Sprint information and active sprint details
            - recent_activity: Recent activity across all artifacts
            - health_status: Overall project health indicators
        """
        summary = {
            "project_config": self._get_project_config(),
            "agile_config": self._get_agile_config(),
            "stories": self._get_story_statistics(),
            "tasks": self._get_task_statistics(),
            "epics": self._get_epic_statistics(),
            "sprints": self._get_sprint_information(),
            "recent_activity": self._get_recent_activity(),
            "health_status": self._get_health_status()
        }
        
        return summary
    
    def _get_project_config(self) -> Dict[str, Any]:
        """Get project configuration information."""
        try:
            config = self.config_service.get_project_config()
            return {
                "name": config.get("name", "N/A"),
                "version": config.get("version", "N/A"),
                "available": True
            }
        except Exception as e:
            return {
                "name": "N/A",
                "version": "N/A", 
                "available": False,
                "error": str(e)
            }
    
    def _get_agile_config(self) -> Dict[str, Any]:
        """Get agile configuration information."""
        try:
            config = self.config_service.get_agile_config()
            return {
                "methodology": config.get("methodology", "N/A"),
                "sprint_duration_weeks": config.get("sprint_duration_weeks", "N/A"),
                "story_point_scale": config.get("story_point_scale", "N/A"),
                "available": True
            }
        except Exception as e:
            return {
                "methodology": "N/A",
                "sprint_duration_weeks": "N/A",
                "story_point_scale": "N/A",
                "available": False,
                "error": str(e)
            }
    
    def _get_story_statistics(self) -> Dict[str, Any]:
        """Get story statistics and counts."""
        try:
            stories = self.story_service.list_stories()
            if stories is None:
                stories = []
            
            story_counts = {"todo": 0, "in_progress": 0, "done": 0, "cancelled": 0, "in_review": 0, "blocked": 0}
            total_points = 0
            
            for story in stories:
                status_key = story.status.value
                story_counts[status_key] = story_counts.get(status_key, 0) + 1
                if story.points:
                    total_points += story.points
            
            return {
                "total": len(stories),
                "counts": story_counts,
                "total_points": total_points,
                "available": True
            }
        except Exception as e:
            return {
                "total": 0,
                "counts": {"todo": 0, "in_progress": 0, "done": 0, "cancelled": 0, "in_review": 0, "blocked": 0},
                "total_points": 0,
                "available": False,
                "error": str(e)
            }
    
    def _get_task_statistics(self) -> Dict[str, Any]:
        """Get task statistics and counts."""
        try:
            tasks = self.task_service.list_tasks()
            if tasks is None:
                tasks = []
            
            task_counts = {"todo": 0, "in_progress": 0, "done": 0, "cancelled": 0, "in_review": 0, "blocked": 0}
            
            for task in tasks:
                status_key = task.status.value
                task_counts[status_key] = task_counts.get(status_key, 0) + 1
            
            return {
                "total": len(tasks),
                "counts": task_counts,
                "available": True
            }
        except Exception as e:
            return {
                "total": 0,
                "counts": {"todo": 0, "in_progress": 0, "done": 0, "cancelled": 0, "in_review": 0, "blocked": 0},
                "available": False,
                "error": str(e)
            }
    
    def _get_epic_statistics(self) -> Dict[str, Any]:
        """Get epic statistics and counts."""
        try:
            epics = self.epic_service.list_epics()
            if epics is None:
                epics = []
            
            epic_counts = {"planning": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
            
            for epic in epics:
                status_key = epic.status.value
                epic_counts[status_key] = epic_counts.get(status_key, 0) + 1
            
            return {
                "total": len(epics),
                "counts": epic_counts,
                "available": True
            }
        except Exception as e:
            return {
                "total": 0,
                "counts": {"planning": 0, "in_progress": 0, "completed": 0, "cancelled": 0},
                "available": False,
                "error": str(e)
            }
    
    def _get_sprint_information(self) -> Dict[str, Any]:
        """Get sprint information and active sprint details."""
        try:
            sprints = self.sprint_service.list_sprints()
            if sprints is None:
                sprints = []
            
            active_sprints = [s for s in sprints if s.status.value == "active"]
            
            # Get detailed information for active sprints
            active_sprint_details = []
            for sprint in active_sprints:
                try:
                    progress = self.sprint_service.get_sprint_progress(sprint.id)
                    active_sprint_details.append({
                        "name": sprint.name,
                        "id": sprint.id,
                        "progress": progress,
                        "available": True
                    })
                except Exception as e:
                    active_sprint_details.append({
                        "name": sprint.name,
                        "id": sprint.id,
                        "progress": None,
                        "available": False,
                        "error": str(e)
                    })
            
            return {
                "total": len(sprints),
                "active_count": len(active_sprints),
                "active_sprints": active_sprint_details,
                "available": True
            }
        except Exception as e:
            return {
                "total": 0,
                "active_count": 0,
                "active_sprints": [],
                "available": False,
                "error": str(e)
            }
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """Get recent activity across all artifacts."""
        try:
            all_items = []
            
            # Collect stories
            try:
                stories = self.story_service.list_stories()
                if stories:
                    for story in stories:
                        all_items.append(("Story", story.title, story.updated_at))
            except Exception:
                pass
            
            # Collect tasks
            try:
                tasks = self.task_service.list_tasks()
                if tasks:
                    for task in tasks:
                        all_items.append(("Task", task.title, task.updated_at))
            except Exception:
                pass
            
            # Collect epics
            try:
                epics = self.epic_service.list_epics()
                if epics:
                    for epic in epics:
                        all_items.append(("Epic", epic.title, epic.updated_at))
            except Exception:
                pass
            
            # Collect sprints
            try:
                sprints = self.sprint_service.list_sprints()
                if sprints:
                    for sprint in sprints:
                        all_items.append(("Sprint", sprint.name, sprint.updated_at))
            except Exception:
                pass
            
            # Sort by date (most recent first) and take top 5
            recent_items = sorted(all_items, key=lambda x: x[2], reverse=True)[:5]
            
            return {
                "items": [
                    {
                        "type": item_type,
                        "title": title,
                        "updated_at": updated_at
                    }
                    for item_type, title, updated_at in recent_items
                ],
                "available": True
            }
        except Exception as e:
            return {
                "items": [],
                "available": False,
                "error": str(e)
            }
    
    def _get_health_status(self) -> Dict[str, Any]:
        """Get overall project health indicators."""
        health_issues = []
        
        # Check if we can access basic services
        try:
            self.config_service.get_project_config()
        except Exception:
            health_issues.append("Project configuration not accessible")
        
        try:
            stories = self.story_service.list_stories()
            if stories is None:
                health_issues.append("Story service returned None")
        except Exception as e:
            health_issues.append(f"Story service error: {str(e)}")
        
        try:
            tasks = self.task_service.list_tasks()
            if tasks is None:
                health_issues.append("Task service returned None")
        except Exception as e:
            health_issues.append(f"Task service error: {str(e)}")
        
        return {
            "is_healthy": len(health_issues) == 0,
            "issues": health_issues,
            "issue_count": len(health_issues)
        } 