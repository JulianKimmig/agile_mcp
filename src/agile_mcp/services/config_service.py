"""Configuration service for agile project management."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
import yaml

from ..storage.filesystem import AgileProjectManager

log = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing project configuration."""

    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the configuration service.

        Args:
            project_manager: The project manager instance
        """
        self.project_manager = project_manager
        self._config_cache: Optional[Dict[str, Any]] = None

    def get_config_path(self) -> Path:
        """Get the path to the config.yml file.

        Returns:
            Path to config.yml
        """
        return self.project_manager.get_agile_dir() / "config.yml"

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load configuration from config.yml.

        Args:
            force_reload: Force reload from disk even if cached

        Returns:
            Configuration dictionary
        """
        if self._config_cache is not None and not force_reload:
            return self._config_cache

        config_path = self.get_config_path()

        if not config_path.exists():
            log.warning(f"Config file not found at {config_path}, creating default")
            self.project_manager._create_default_config()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config_cache = yaml.safe_load(f) or {}
            log.debug(f"Loaded configuration from {config_path}")
            return self._config_cache
        except Exception as e:
            log.error(f"Failed to load configuration: {e}")
            # Return default config if loading fails
            return self._get_default_config()

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to config.yml.

        Args:
            config: Configuration dictionary to save
        """
        config_path = self.get_config_path()

        try:
            # Ensure the directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            # Update cache
            self._config_cache = config
            log.debug(f"Configuration saved to {config_path}")

        except Exception as e:
            log.error(f"Failed to save configuration: {e}")
            raise

    def get_project_config(self) -> Dict[str, Any]:
        """Get project-specific configuration.

        Returns:
            Project configuration dictionary
        """
        config = self.load_config()
        return config.get("project", {})

    def get_agile_config(self) -> Dict[str, Any]:
        """Get agile methodology configuration.

        Returns:
            Agile configuration dictionary
        """
        config = self.load_config()
        return config.get("agile", {})

    def get_story_point_scale(self) -> List[int]:
        """Get the story point scale from configuration.

        Returns:
            List of valid story point values
        """
        agile_config = self.get_agile_config()
        return agile_config.get("story_point_scale", [1, 2, 3, 5, 8, 13, 21])

    def get_sprint_duration_weeks(self) -> int:
        """Get default sprint duration in weeks.

        Returns:
            Sprint duration in weeks
        """
        agile_config = self.get_agile_config()
        return agile_config.get("sprint_duration_weeks", 2)

    def get_methodology(self) -> str:
        """Get the agile methodology.

        Returns:
            Methodology name (e.g., 'scrum', 'kanban')
        """
        agile_config = self.get_agile_config()
        return agile_config.get("methodology", "scrum")

    def get_project_name(self) -> str:
        """Get the project name.

        Returns:
            Project name
        """
        project_config = self.get_project_config()
        return project_config.get("name", self.project_manager.project_path.name)

    def get_project_version(self) -> str:
        """Get the project version.

        Returns:
            Project version
        """
        project_config = self.get_project_config()
        return project_config.get("version", "1.0.0")

    def update_project_config(self, **kwargs) -> None:
        """Update project configuration.

        Args:
            **kwargs: Configuration keys and values to update
        """
        config = self.load_config()
        if "project" not in config:
            config["project"] = {}

        config["project"].update(kwargs)
        self.save_config(config)

    def update_agile_config(self, **kwargs) -> None:
        """Update agile methodology configuration.

        Args:
            **kwargs: Configuration keys and values to update
        """
        config = self.load_config()
        if "agile" not in config:
            config["agile"] = {}

        config["agile"].update(kwargs)
        self.save_config(config)

    def validate_story_points(self, points: int) -> bool:
        """Validate if story points value is valid according to configuration.

        Args:
            points: Story points value to validate

        Returns:
            True if valid, False otherwise
        """
        scale = self.get_story_point_scale()
        return points in scale

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if loading fails.

        Returns:
            Default configuration dictionary
        """
        return {
            "project": {
                "name": self.project_manager.project_path.name,
                "version": "1.0.0",
                "created_at": "auto-generated",
            },
            "agile": {"methodology": "scrum", "story_point_scale": [1, 2, 3, 5, 8, 13, 21], "sprint_duration_weeks": 2},
        }

    def get_full_config(self) -> Dict[str, Any]:
        """Get the complete configuration.

        Returns:
            Full configuration dictionary
        """
        return self.load_config()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        default_config = self._get_default_config()
        self.save_config(default_config)
        log.info("Configuration reset to defaults")
