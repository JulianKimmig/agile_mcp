"""Tests for base AgileArtifact model."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from agile_mcp.models.base import AgileArtifact


class TestAgileArtifact:
    """Test cases for the AgileArtifact base model."""

    def test_create_agile_artifact_with_required_fields(self) -> None:
        """Test creating an AgileArtifact with only required fields."""
        artifact = AgileArtifact(id="TEST-001")

        assert artifact.id == "TEST-001"
        assert isinstance(artifact.created_at, datetime)
        assert isinstance(artifact.updated_at, datetime)
        assert artifact.created_by is None
        assert artifact.tags == []

    def test_create_agile_artifact_with_all_fields(self) -> None:
        """Test creating an AgileArtifact with all fields."""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        updated_at = datetime(2024, 1, 2, 12, 0, 0)

        artifact = AgileArtifact(
            id="TEST-002",
            created_at=created_at,
            updated_at=updated_at,
            created_by="test_user",
            tags=["urgent", "feature"],
        )

        assert artifact.id == "TEST-002"
        assert artifact.created_at == created_at
        assert artifact.updated_at == updated_at
        assert artifact.created_by == "test_user"
        assert artifact.tags == ["urgent", "feature"]

    def test_agile_artifact_auto_timestamps(self) -> None:
        """Test that timestamps are automatically set if not provided."""
        before_creation = datetime.now()
        artifact = AgileArtifact(id="TEST-003")
        after_creation = datetime.now()

        assert before_creation <= artifact.created_at <= after_creation
        assert before_creation <= artifact.updated_at <= after_creation

    def test_agile_artifact_requires_id(self) -> None:
        """Test that AgileArtifact requires an ID."""
        with pytest.raises(ValidationError) as exc_info:
            AgileArtifact()

        assert "id" in str(exc_info.value)

    def test_agile_artifact_id_must_be_string(self) -> None:
        """Test that ID must be a string."""
        with pytest.raises(ValidationError) as exc_info:
            AgileArtifact(id=123)

        assert "str_type" in str(exc_info.value) or "string" in str(exc_info.value).lower()

    def test_agile_artifact_tags_default_empty_list(self) -> None:
        """Test that tags default to empty list."""
        artifact = AgileArtifact(id="TEST-004")
        assert artifact.tags == []

        # Ensure it's a new list, not shared reference
        artifact.tags.append("test")
        artifact2 = AgileArtifact(id="TEST-005")
        assert artifact2.tags == []

    def test_agile_artifact_serialization(self) -> None:
        """Test that AgileArtifact can be serialized to dict and JSON."""
        artifact = AgileArtifact(id="TEST-006", created_by="test_user", tags=["test"])

        # Test dict serialization
        artifact_dict = artifact.model_dump()
        assert artifact_dict["id"] == "TEST-006"
        assert artifact_dict["created_by"] == "test_user"
        assert artifact_dict["tags"] == ["test"]
        assert "created_at" in artifact_dict
        assert "updated_at" in artifact_dict

        # Test JSON serialization
        json_str = artifact.model_dump_json()
        assert "TEST-006" in json_str
        assert "test_user" in json_str
