# Agile-MCP API Reference

This document provides comprehensive documentation for all MCP tools available in the agile-mcp system.

## Project Management Tools

### set_project
Set the project directory for agile project management.

**Parameters:**
- `project_path` (string, required): Path to the project directory. Can be relative or absolute. Use '.' for current directory.

**Returns:**
Success message with the resolved project path.

**Example:**
```
project_path: "."
```

### get_project
Get the current project directory.

**Parameters:**
None

**Returns:**
Current project directory path or message if not set.

## Story Management Tools

### create_story
Create a new user story in the agile project.

**Parameters:**
- `title` (string, required): Story title
- `description` (string, required): Story description
- `priority` (string, optional): Story priority (default: "medium"). Valid values: "low", "medium", "high", "critical"
- `points` (integer, optional): Story points - must be Fibonacci number (1, 2, 3, 5, 8, 13, 21)
- `tags` (string, optional): Comma-separated tags

**Returns:**
Success message with story details and generated ID.

**Example:**
```
title: "User Authentication"
description: "Implement secure user login and registration"
priority: "high"
points: 8
tags: "authentication, security, backend"
```

### get_story
Retrieve a user story by its ID.

**Parameters:**
- `story_id` (string, required): The ID of the story to retrieve

**Returns:**
Success message with story details.

**Example:**
```
story_id: "STORY-ABC123"
```

### update_story
Update an existing user story.

**Parameters:**
- `story_id` (string, required): The ID of the story to update
- `title` (string, optional): New story title
- `description` (string, optional): New story description
- `priority` (string, optional): New priority ("low", "medium", "high", "critical")
- `status` (string, optional): New status ("todo", "in_progress", "done", "blocked")
- `points` (integer, optional): New story points (Fibonacci number)
- `tags` (string, optional): New comma-separated tags

**Returns:**
Success message with updated story details.

**Example:**
```
story_id: "STORY-ABC123"
status: "in_progress"
priority: "high"
```

### list_stories
List user stories with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status ("todo", "in_progress", "done", "blocked")
- `priority` (string, optional): Filter by priority ("low", "medium", "high", "critical")
- `sprint_id` (string, optional): Filter by sprint ID

**Returns:**
Success message with list of stories matching the filters.

**Example:**
```
status: "in_progress"
priority: "high"
```

### delete_story
Delete a user story by its ID.

**Parameters:**
- `story_id` (string, required): The ID of the story to delete

**Returns:**
Success message confirming deletion.

**Example:**
```
story_id: "STORY-ABC123"
```

## Sprint Management Tools

### create_sprint
Create a new sprint.

**Parameters:**
- `name` (string, required): Sprint name
- `goal` (string, optional): Sprint goal or objective
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `tags` (string, optional): Comma-separated tags

**Returns:**
Success message with sprint details and generated ID.

**Example:**
```
name: "Sprint 1 - Foundation"
goal: "Establish core functionality"
start_date: "2025-01-07"
end_date: "2025-01-21"
tags: "foundation, core"
```

### get_sprint
Retrieve a sprint by its ID.

**Parameters:**
- `sprint_id` (string, required): The ID of the sprint to retrieve

**Returns:**
Success message with sprint details and progress information.

**Example:**
```
sprint_id: "SPRINT-XYZ789"
```

### update_sprint
Update an existing sprint.

**Parameters:**
- `sprint_id` (string, required): The ID of the sprint to update
- `name` (string, optional): New sprint name
- `goal` (string, optional): New sprint goal
- `status` (string, optional): New status ("planning", "active", "completed", "cancelled")
- `start_date` (string, optional): New start date in YYYY-MM-DD format
- `end_date` (string, optional): New end date in YYYY-MM-DD format
- `tags` (string, optional): New comma-separated tags

**Returns:**
Success message with updated sprint details.

**Example:**
```
sprint_id: "SPRINT-XYZ789"
status: "active"
```

### list_sprints
List sprints with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status ("planning", "active", "completed", "cancelled")
- `include_stories` (boolean, optional): Include story IDs in results (default: false)

**Returns:**
Success message with list of sprints matching the filters.

**Example:**
```
status: "active"
include_stories: true
```

### manage_sprint_stories
Add or remove stories from a sprint.

**Parameters:**
- `sprint_id` (string, required): The sprint ID
- `action` (string, required): Either "add" or "remove"
- `story_id` (string, required): The story ID to add or remove

**Returns:**
Success message with updated sprint details.

**Example:**
```
sprint_id: "SPRINT-XYZ789"
action: "add"
story_id: "STORY-ABC123"
```

### get_sprint_progress
Get detailed progress information for a sprint.

**Parameters:**
- `sprint_id` (string, required): The sprint ID to get progress for

**Returns:**
Success message with detailed progress information including time elapsed, story completion, etc.

**Example:**
```
sprint_id: "SPRINT-XYZ789"
```

### get_active_sprint
Get the currently active sprint.

**Parameters:**
None

**Returns:**
Success message with active sprint details and progress, or message if no active sprint exists.

## Task Management Tools

### create_task
Create a new task.

**Parameters:**
- `title` (string, required): Task title
- `description` (string, required): Task description
- `story_id` (string, optional): ID of the parent story
- `assignee` (string, optional): Person assigned to this task
- `due_date` (string, optional): Task due date in YYYY-MM-DD format
- `estimated_hours` (float, optional): Estimated hours to complete
- `priority` (string, optional): Task priority (default: "medium"). Valid values: "low", "medium", "high", "critical"
- `tags` (string, optional): Comma-separated tags

**Returns:**
Success message with task details.

**Example:**
```
title: "Implement User Login UI"
description: "Develop the frontend UI for user login."
story_id: "STORY-ABC123"
assignee: "John Doe"
due_date: "2025-07-15"
estimated_hours: 8.0
priority: "high"
tags: "frontend, UI"
```

### get_task
Get a task by ID.

**Parameters:**
- `task_id` (string, required): The ID of the task to retrieve

**Returns:**
Success message with task details.

**Example:**
```
task_id: "TASK-XYZ789"
```

### update_task
Update an existing task.

**Parameters:**
- `task_id` (string, required): The ID of the task to update
- `title` (string, optional): New task title
- `description` (string, optional): New task description
- `status` (string, optional): New status ("todo", "in_progress", "done", "blocked")
- `priority` (string, optional): New priority ("low", "medium", "high", "critical")
- `assignee` (string, optional): New assignee
- `due_date` (string, optional): New due date in YYYY-MM-DD format
- `estimated_hours` (float, optional): New estimated hours
- `actual_hours` (float, optional): Actual hours spent
- `dependencies` (string, optional): New comma-separated dependencies
- `tags` (string, optional): New comma-separated tags

**Returns:**
Success message with updated task details.

**Example:**
```
task_id: "TASK-XYZ789"
status: "in_progress"
actual_hours: 4.0
```

### list_tasks
List tasks with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status ("todo", "in_progress", "done", "blocked")
- `priority` (string, optional): Filter by priority ("low", "medium", "high", "critical")
- `story_id` (string, optional): Filter by parent story ID
- `assignee` (string, optional): Filter by assignee
- `include_completed` (boolean, optional): Include completed tasks (default: true)

**Returns:**
Success message with list of tasks matching the filters.

**Example:**
```
status: "in_progress"
assignee: "John Doe"
```

### delete_task
Delete a task by ID.

**Parameters:**
- `task_id` (string, required): The ID of the task to delete

**Returns:**
Success message confirming deletion.

**Example:**
```
task_id: "TASK-XYZ789"
```

## Epic Management Tools

### create_epic
Create a new epic.

**Parameters:**
- `title` (string, required): Epic title
- `description` (string, required): Epic description
- `status` (string, optional): Epic status (default: "planning"). Valid values: "planning", "in_progress", "completed", "on_hold"
- `tags` (string, optional): Comma-separated tags

**Returns:**
Success message with epic details.

**Example:**
```
title: "User Management System"
description: "Develop a complete system for user registration, login, and profile management."
status: "in_progress"
tags: "backend, security"
```

### get_epic
Get an epic by ID.

**Parameters:**
- `epic_id` (string, required): The ID of the epic to retrieve

**Returns:**
Success message with epic details.

**Example:**
```
epic_id: "EPIC-12345"
```

### update_epic
Update an existing epic.

**Parameters:**
- `epic_id` (string, required): The ID of the epic to update
- `title` (string, optional): New epic title
- `description` (string, optional): New epic description
- `status` (string, optional): New status ("planning", "in_progress", "completed", "on_hold")
- `tags` (string, optional): New comma-separated tags

**Returns:**
Success message with updated epic details.

**Example:**
```
epic_id: "EPIC-12345"
status: "completed"
```

### list_epics
List epics with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status ("planning", "in_progress", "completed", "on_hold")
- `include_stories` (boolean, optional): Include story IDs in results (default: false)

**Returns:**
Success message with list of epics matching the filters.

**Example:**
```
status: "in_progress"
include_stories: true
```

### delete_epic
Delete an epic by ID.

**Parameters:**
- `epic_id` (string, required): The ID of the epic to delete

**Returns:**
Success message confirming deletion.

**Example:**
```
epic_id: "EPIC-12345"
```

### manage_epic_stories
Add or remove stories from an epic.

**Parameters:**
- `epic_id` (string, required): The epic ID
- `action` (string, required): Either "add" or "remove"
- `story_id` (string, required): The story ID to add or remove

**Returns:**
Success message with updated epic details.

**Example:**
```
epic_id: "EPIC-12345"
action: "add"
story_id: "STORY-ABC123"
```

## Product Backlog Tools

### get_product_backlog
Get the product backlog with optional filtering.

**Parameters:**
- `priority` (string, optional): Filter by priority ("low", "medium", "high", "critical")
- `tags` (string, optional): Filter by comma-separated tags
- `include_completed` (boolean, optional): Include completed stories (default: false)

**Returns:**
Success message with product backlog.

**Example:**
```
priority: "high"
include_completed: false
```

## Burndown Chart Tools

### get_sprint_burndown_chart
Get a burndown chart for a specific sprint.

**Parameters:**
- `sprint_id` (string, required): The ID of the sprint to get the burndown chart for

**Returns:**
A string representation of the burndown chart.

**Example:**
```
sprint_id: "SPRINT-XYZ789"
```

## Data Models

### Task Status Values
- `todo`: Task is planned but not started
- `in_progress`: Task is currently being worked on
- `done`: Task is completed
- `blocked`: Task is blocked by dependencies

### Task Priority Values
- `low`: Low priority task
- `medium`: Medium priority task (default)
- `high`: High priority task
- `critical`: Critical priority task

### Epic Status Values
- `planning`: Epic is in planning phase
- `in_progress`: Epic is currently active
- `completed`: Epic has been completed
- `cancelled`: Epic was cancelled



### Story Status Values
- `todo`: Story is planned but not started
- `in_progress`: Story is currently being worked on
- `done`: Story is completed
- `blocked`: Story is blocked by dependencies

### Story Priority Values
- `low`: Low priority story
- `medium`: Medium priority story (default)
- `high`: High priority story
- `critical`: Critical priority story

### Sprint Status Values
- `planning`: Sprint is in planning phase
- `active`: Sprint is currently active
- `completed`: Sprint has been completed
- `cancelled`: Sprint was cancelled

### Story Points
Story points must be Fibonacci numbers: 1, 2, 3, 5, 8, 13, 21

## Error Handling

All tools return descriptive error messages when:
- Required parameters are missing
- Invalid parameter values are provided
- Resources (stories/sprints) are not found
- Project is not properly initialized

## Usage Examples

### Basic Workflow
1. Set up project: `set_project` with project directory
2. Create stories: `create_story` with title and description
3. Create sprint: `create_sprint` with name and goal
4. Add stories to sprint: `manage_sprint_stories` to add stories
5. Start sprint: `update_sprint` to set status to "active"
6. Track progress: `get_sprint_progress` and `get_active_sprint`
7. Update story status: `update_story` as work progresses
8. Complete sprint: `update_sprint` to set status to "completed"
