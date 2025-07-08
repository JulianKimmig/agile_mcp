"""Service layer for user story management."""

import sys

from ..models.story import Priority, StoryStatus, UserStory
from ..storage.filesystem import AgileProjectManager
from ..utils.id_generator import generate_story_id


class StoryService:
    """Service for managing user stories with file-based persistence."""

    # Fibonacci sequence for story points validation
    VALID_FIBONACCI_POINTS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 134]

    def __init__(self, project_manager: AgileProjectManager):
        """Initialize the story service.

        Args:
            project_manager: The project manager for file operations
        """
        self.project_manager = project_manager
        self.stories_dir = project_manager.get_stories_dir()

    def create_story(
        self,
        title: str,
        description: str,
        priority: Priority = Priority.MEDIUM,
        status: StoryStatus = StoryStatus.TODO,
        points: int | None = None,
        sprint_id: str | None = None,
        tags: list[str] | None = None,
    ) -> UserStory:
        """Create a new user story.

        Args:
            title: Story title
            description: Story description
            priority: Story priority (default: MEDIUM)
            status: Story status (default: TODO)
            points: Story points (must be Fibonacci number)
            sprint_id: Associated sprint ID
            tags: List of tags

        Returns:
            The created UserStory

        Raises:
            ValueError: If points is not a valid Fibonacci number
        """
        # Validate story points
        if points:
            points = int(points)
        if points and points not in self.VALID_FIBONACCI_POINTS:
            raise ValueError(f"Story points must be a Fibonacci number: {self.VALID_FIBONACCI_POINTS}")

        # Generate unique ID
        story_id = generate_story_id()

        # Create story instance
        story = UserStory(
            id=story_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            points=points,
            sprint_id=sprint_id,
            tags=tags or [],
        )

        # Persist to file using storage layer
        self.project_manager.save_story(story)

        return story

    def get_story(self, story_id: str) -> UserStory | None:
        """Retrieve a story by ID.

        Args:
            story_id: The story ID to retrieve

        Returns:
            The UserStory if found, None otherwise
        """
        return self.project_manager.get_story(story_id)

    def update_story(
        self,
        story_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        status: StoryStatus | None = None,
        points: int | None = None,
        sprint_id: str | None = None,
        tags: list[str] | None = None,
    ) -> UserStory | None:
        """Update an existing story.

        Args:
            story_id: ID of the story to update
            title: New title (optional)
            description: New description (optional)
            priority: New priority (optional)
            status: New status (optional)
            points: New points (optional, must be Fibonacci)
            sprint_id: New sprint ID (optional)
            tags: New tags (optional)

        Returns:
            The updated UserStory if found, None otherwise

        Raises:
            ValueError: If points is not a valid Fibonacci number
        """
        story = self.get_story(story_id)
        if story is None:
            return None

        # Validate story points if provided
        if points and points not in self.VALID_FIBONACCI_POINTS:
            raise ValueError(f"Story points must be a Fibonacci number: {self.VALID_FIBONACCI_POINTS}")

        # Update fields that were provided
        update_data = {}
        if title:
            update_data["title"] = title
        if description:
            update_data["description"] = description
        if priority:
            update_data["priority"] = priority
        if status:
            update_data["status"] = status
        if points:
            update_data["points"] = points  # type: ignore
        if sprint_id:
            update_data["sprint_id"] = sprint_id
        if tags:
            update_data["tags"] = tags

        # Create updated story
        updated_story = story.model_copy(update=update_data)

        # Persist changes using storage layer
        self.project_manager.save_story(updated_story)

        return updated_story

    def delete_story(self, story_id: str) -> bool:
        """Delete a story by ID and clean up references.

        Args:
            story_id: ID of the story to delete

        Returns:
            True if story was deleted, False if not found
        """
        # Check if story exists first
        story = self.get_story(story_id)
        if not story:
            return False

        # Remove story from any sprints that contain it
        self._cleanup_sprint_references(story_id)

        # Remove story from any epics that contain it
        self._cleanup_epic_references(story_id)

        # Delete the story
        deleted = self.project_manager.delete_story(story_id)

        if deleted:
            print(f"Info: Story {story_id} deleted and removed from all sprint and epic references", file=sys.stderr)

        return deleted

    def list_stories(
        self,
        status: StoryStatus | None = None,
        priority: Priority | None = None,
        sprint_id: str | None = None,
        _filter_no_sprint: bool = False,
    ) -> list[UserStory]:
        """List stories with optional filtering.

        Args:
            status: Filter by status (optional). Options :TODO, IN_PROGRESS, DONE, BLOCKED
            priority: Filter by priority (optional). Options :LOW, MEDIUM, HIGH, CRITICAL
            sprint_id: Filter by sprint ID (optional)
            _filter_no_sprint: Internal flag to filter stories with no sprint

        Returns:
            List of UserStory objects matching the filters
        """

        # Get all stories from storage layer
        stories = self.project_manager.list_stories()

        # Apply filters
        filtered_stories = []
        for story in stories:
            if status and story.status != status:
                continue

            if priority and story.priority != priority:
                continue

            # Sprint filtering logic
            if sprint_id:
                if story.sprint_id != sprint_id:
                    continue
            elif _filter_no_sprint:
                # Filter for stories with no sprint assignment
                if story.sprint_id:
                    continue

            filtered_stories.append(story)

        stories = filtered_stories

        return stories

    def _cleanup_sprint_references(self, story_id: str) -> None:
        """Remove story from all sprints that contain it.

        Args:
            story_id: ID of the story to remove from sprints
        """
        # Get all sprints to check for references
        sprints = self.project_manager.list_sprints()

        for sprint in sprints:
            if story_id in sprint.story_ids:
                # Remove story from sprint
                updated_story_ids = [sid for sid in sprint.story_ids if sid != story_id]
                updated_sprint = sprint.model_copy(update={"story_ids": updated_story_ids})
                updated_sprint.updated_at = updated_sprint.updated_at  # Keep existing timestamp

                # Save updated sprint
                self.project_manager.save_sprint(updated_sprint)

                print(f"Info: Removed story {story_id} from sprint {sprint.id}", file=sys.stderr)

    def _cleanup_epic_references(self, story_id: str) -> None:
        """Remove story from all epics that contain it.

        Args:
            story_id: ID of the story to remove from epics
        """
        # Get all epics to check for references
        epics = self.project_manager.list_epics()

        for epic in epics:
            if story_id in epic.story_ids:
                # Remove story from epic
                updated_story_ids = [sid for sid in epic.story_ids if sid != story_id]
                updated_epic = epic.model_copy(update={"story_ids": updated_story_ids})
                updated_epic.updated_at = updated_epic.updated_at  # Keep existing timestamp

                # Save updated epic
                self.project_manager.save_epic(updated_epic)

                print(f"Info: Removed story {story_id} from epic {epic.id}", file=sys.stderr)
