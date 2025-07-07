"""Centralized ID generation utility for Agile MCP artifacts.

This module provides a single source of truth for generating unique IDs
across all artifact types (stories, tasks, sprints, epics) in the system.
"""

import secrets


def generate_id(prefix: str) -> str:
    """Generate a unique ID with the specified prefix.
    
    Creates an ID in the format: PREFIX-XXXXXXXX where XXXXXXXX is an 8-character
    hexadecimal string generated using cryptographically secure random bytes.
    
    Args:
        prefix: The prefix to use for the ID (e.g., "STORY", "TASK", "SPRINT", "EPIC")
        
    Returns:
        A unique ID string in the format PREFIX-XXXXXXXX
        
    Examples:
        >>> generate_id("STORY")
        'STORY-A1B2C3D4'
        >>> generate_id("TASK")
        'TASK-E5F6G7H8'
    """
    if not prefix:
        raise ValueError("Prefix cannot be empty")
    
    # Generate 4 random bytes and convert to 8-character hex string
    random_hex = secrets.token_hex(4).upper()
    
    return f"{prefix}-{random_hex}"


def generate_story_id() -> str:
    """Generate a unique story ID.
    
    Returns:
        A unique story ID in the format STORY-XXXXXXXX
    """
    return generate_id("STORY")


def generate_task_id() -> str:
    """Generate a unique task ID.
    
    Returns:
        A unique task ID in the format TASK-XXXXXXXX
    """
    return generate_id("TASK")


def generate_sprint_id() -> str:
    """Generate a unique sprint ID.
    
    Returns:
        A unique sprint ID in the format SPRINT-XXXXXXXX
    """
    return generate_id("SPRINT")


def generate_epic_id() -> str:
    """Generate a unique epic ID.
    
    Returns:
        A unique epic ID in the format EPIC-XXXXXXXX
    """
    return generate_id("EPIC") 