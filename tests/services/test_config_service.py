"""Tests for configuration service."""

import pytest
import tempfile
from pathlib import Path

from agile_mcp.storage.filesystem import AgileProjectManager
from agile_mcp.services.config_service import ConfigurationService


class TestConfigurationService:
    """Test cases for the ConfigurationService."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def project_manager(self, temp_project_dir):
        """Create a project manager for testing."""
        manager = AgileProjectManager(temp_project_dir)
        manager.initialize()
        return manager

    @pytest.fixture
    def config_service(self, project_manager):
        """Create a configuration service for testing."""
        return ConfigurationService(project_manager)

    def test_config_service_initialization(self, config_service, project_manager):
        """Test configuration service initialization."""
        assert config_service.project_manager == project_manager
        assert config_service._config_cache is None

    def test_get_config_path(self, config_service, project_manager):
        """Test getting configuration file path."""
        expected_path = project_manager.get_agile_dir() / "config.yml"
        assert config_service.get_config_path() == expected_path

    def test_load_config_creates_default_if_missing(self, config_service):
        """Test that load_config creates default config if file doesn't exist."""
        config = config_service.load_config()

        # Should have default structure
        assert "project" in config
        assert "agile" in config
        assert config["project"]["name"] == config_service.project_manager.project_path.name
        assert config["agile"]["methodology"] == "scrum"
        assert config["agile"]["story_point_scale"] == [1, 2, 3, 5, 8, 13, 21]

    def test_load_config_caching(self, config_service):
        """Test that configuration is cached after first load."""
        # First load
        config1 = config_service.load_config()

        # Second load should return cached version
        config2 = config_service.load_config()

        assert config1 is config2  # Same object reference

    def test_load_config_force_reload(self, config_service):
        """Test force reload bypasses cache."""
        # Load config first
        config_service.load_config()

        # Modify cache to test force reload
        config_service._config_cache["test_key"] = "test_value"

        # Force reload should get fresh config without test_key
        config = config_service.load_config(force_reload=True)
        assert "test_key" not in config

    def test_save_config(self, config_service):
        """Test saving configuration."""
        test_config = {
            "project": {"name": "test_project", "version": "2.0.0"},
            "agile": {"methodology": "kanban", "sprint_duration_weeks": 3},
        }

        config_service.save_config(test_config)

        # Verify config was saved and cached
        assert config_service._config_cache == test_config

        # Verify config can be loaded from disk
        loaded_config = config_service.load_config(force_reload=True)
        assert loaded_config == test_config

    def test_get_project_config(self, config_service):
        """Test getting project-specific configuration."""
        project_config = config_service.get_project_config()

        assert isinstance(project_config, dict)
        assert "name" in project_config
        assert "version" in project_config

    def test_get_agile_config(self, config_service):
        """Test getting agile methodology configuration."""
        agile_config = config_service.get_agile_config()

        assert isinstance(agile_config, dict)
        assert "methodology" in agile_config
        assert "story_point_scale" in agile_config

    def test_get_story_point_scale(self, config_service):
        """Test getting story point scale."""
        scale = config_service.get_story_point_scale()

        assert isinstance(scale, list)
        assert scale == [1, 2, 3, 5, 8, 13, 21]  # Default Fibonacci

    def test_get_sprint_duration_weeks(self, config_service):
        """Test getting sprint duration."""
        duration = config_service.get_sprint_duration_weeks()

        assert isinstance(duration, int)
        assert duration == 2  # Default

    def test_get_methodology(self, config_service):
        """Test getting methodology."""
        methodology = config_service.get_methodology()

        assert isinstance(methodology, str)
        assert methodology == "scrum"  # Default

    def test_get_project_name(self, config_service):
        """Test getting project name."""
        name = config_service.get_project_name()

        assert isinstance(name, str)
        assert name == config_service.project_manager.project_path.name

    def test_get_project_version(self, config_service):
        """Test getting project version."""
        version = config_service.get_project_version()

        assert isinstance(version, str)
        assert version == "1.0.0"  # Default

    def test_update_project_config(self, config_service):
        """Test updating project configuration."""
        config_service.update_project_config(name="updated_name", version="3.0.0")

        project_config = config_service.get_project_config()
        assert project_config["name"] == "updated_name"
        assert project_config["version"] == "3.0.0"

    def test_update_agile_config(self, config_service):
        """Test updating agile configuration."""
        config_service.update_agile_config(methodology="kanban", sprint_duration_weeks=1)

        agile_config = config_service.get_agile_config()
        assert agile_config["methodology"] == "kanban"
        assert agile_config["sprint_duration_weeks"] == 1

    def test_validate_story_points_valid(self, config_service):
        """Test validating valid story points."""
        assert config_service.validate_story_points(1) is True
        assert config_service.validate_story_points(5) is True
        assert config_service.validate_story_points(13) is True

    def test_validate_story_points_invalid(self, config_service):
        """Test validating invalid story points."""
        assert config_service.validate_story_points(4) is False
        assert config_service.validate_story_points(6) is False
        assert config_service.validate_story_points(100) is False

    def test_validate_story_points_custom_scale(self, config_service):
        """Test validating story points with custom scale."""
        # Update to custom scale
        config_service.update_agile_config(story_point_scale=[1, 2, 4, 8])

        assert config_service.validate_story_points(4) is True
        assert config_service.validate_story_points(8) is True
        assert config_service.validate_story_points(3) is False

    def test_get_full_config(self, config_service):
        """Test getting full configuration."""
        full_config = config_service.get_full_config()

        assert isinstance(full_config, dict)
        assert "project" in full_config
        assert "agile" in full_config

    def test_reset_to_defaults(self, config_service):
        """Test resetting configuration to defaults."""
        # Modify config first
        config_service.update_project_config(name="modified")
        config_service.update_agile_config(methodology="kanban")

        # Reset to defaults
        config_service.reset_to_defaults()

        # Verify defaults are restored
        assert config_service.get_methodology() == "scrum"
        assert config_service.get_project_name() == config_service.project_manager.project_path.name

    def test_load_config_handles_yaml_errors(self, config_service):
        """Test that load_config handles YAML parsing errors gracefully."""
        # Create a malformed YAML file
        config_path = config_service.get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            f.write("invalid: yaml: content:\n  - malformed")

        # Should return default config when parsing fails
        config = config_service.load_config(force_reload=True)

        assert "project" in config
        assert "agile" in config
        assert config["agile"]["methodology"] == "scrum"

    def test_save_config_creates_directory(self, config_service):
        """Test that save_config creates directory if it doesn't exist."""
        # Remove the .agile directory
        agile_dir = config_service.project_manager.get_agile_dir()
        if agile_dir.exists():
            import shutil

            shutil.rmtree(agile_dir)

        test_config = {"project": {"name": "test"}, "agile": {"methodology": "scrum"}}

        # Should create directory and save config
        config_service.save_config(test_config)

        assert agile_dir.exists()
        assert config_service.get_config_path().exists()
