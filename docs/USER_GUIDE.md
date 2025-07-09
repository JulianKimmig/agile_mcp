# Agile-MCP User Guide

Welcome to Agile-MCP! This guide will help you get started with using the agile project management tools through the MCP (Model Context Protocol) interface.

## Getting Started

### 1. Setting Up Your Project

First, you need to set up your project directory where all agile artifacts will be stored:

```
Tool: set_project
Parameters:
  project_path: "."  # Use current directory
```

This creates a `.agile` folder in your project directory to store all stories, sprints, and project data.

### 2. Creating Your First User Story

User stories are the foundation of agile project management. Create your first story:

```
Tool: create_story
Parameters:
  name: "User Authentication System"
  description: "Implement secure user login and registration functionality"
  priority: "high"
  tags: "authentication, security"
```

### 3. Creating a Sprint

Sprints are time-boxed iterations where you work on a set of stories:

```
Tool: create_sprint
Parameters:
  name: "Sprint 1 - Authentication"
  goal: "Implement core authentication features"
  start_date: "2025-01-07"
  end_date: "2025-01-21"
```

### 4. Adding Stories to Your Sprint

Connect your stories to the sprint:

```
Tool: manage_sprint_stories
Parameters:
  sprint_id: "SPRINT-ABC123"  # Use the ID from create_sprint
  action: "add"
  story_id: "STORY-XYZ789"   # Use the ID from create_story
```

### 5. Starting Your Sprint

Make your sprint active to begin working:

```
Tool: update_sprint
Parameters:
  sprint_id: "SPRINT-ABC123"
  status: "active"
```

## Daily Workflow

### Checking Your Active Sprint
```
Tool: get_active_sprint
```

### Updating Story Progress
As you work on stories, update their status:

```
Tool: update_story
Parameters:
  story_id: "STORY-XYZ789"
  status: "in_progress"
```

### Tracking Sprint Progress
```
Tool: get_sprint_progress
Parameters:
  sprint_id: "SPRINT-ABC123"
```

### Listing Stories
Filter stories by status, priority, or sprint:

```
Tool: list_stories
Parameters:
  status: "in_progress"
  priority: "high"
```

## Task Management

Tasks are smaller, actionable items that make up a user story. They help break down work into manageable pieces.

### Creating a Task

```
Tool: create_task
Parameters:
  name: "Design UI Mockups"
  description: "Create wireframes and mockups for the user authentication flow."
  story_id: "STORY-XYZ789" # Link to a parent story
  assignee: "Jane Doe"
  estimated_hours: 4.0
  priority: "high"
```

### Getting a Task

```
Tool: get_task
Parameters:
  task_id: "TASK-ABC123"
```

### Updating Task Progress

```
Tool: update_task
Parameters:
  task_id: "TASK-ABC123"
  status: "in_progress"
  actual_hours: 2.0
```

### Listing Tasks

```
Tool: list_tasks
Parameters:
  story_id: "STORY-XYZ789"
  status: "todo"
```

### Deleting a Task

```
Tool: delete_task
Parameters:
  task_id: "TASK-ABC123"
```

## Epic Management

Epics are large bodies of work that can be broken down into several stories. They represent major initiatives.

### Creating an Epic

```
Tool: create_epic
Parameters:
  name: "User Profile Management"
  description: "Implement all features related to user profiles, including creation, editing, and viewing."
  status: "in_progress"
```

### Getting an Epic

```
Tool: get_epic
Parameters:
  epic_id: "EPIC-DEF456"
```

### Updating an Epic

```
Tool: update_epic
Parameters:
  epic_id: "EPIC-DEF456"
  status: "completed"
```

### Listing Epics

```
Tool: list_epics
Parameters:
  status: "in_progress"
  include_stories: true
```

### Deleting an Epic

```
Tool: delete_epic
Parameters:
  epic_id: "EPIC-DEF456"
```

### Managing Stories in an Epic

```
Tool: manage_epic_stories
Parameters:
  epic_id: "EPIC-DEF456"
  action: "add"
  story_id: "STORY-XYZ789"
```

## Advanced Features

### Product Backlog

The product backlog is a prioritized list of all features, functions, components, and enhancements needed for the product.

```
Tool: get_product_backlog
Parameters:
  priority: "high"
  include_completed: false
```

### Burndown Charts

Burndown charts visualize the remaining work in a sprint against time. They help track progress and predict sprint completion.

```
Tool: get_sprint_burndown_chart
Parameters:
  sprint_id: "SPRINT-ABC123"
```

### Story Points and Estimation

Use Fibonacci numbers to estimate story complexity:

```
Tool: update_story
Parameters:
  story_id: "STORY-XYZ789"
  points: 8  # Must be: 1, 2, 3, 5, 8, 13, or 21
```

### Story Status Management

Track story progress through these statuses:
- `todo` - Story is planned but not started
- `in_progress` - Currently being worked on
- `done` - Story is completed
- `blocked` - Story is blocked by dependencies

### Sprint Management

Manage your sprint lifecycle:
- `planning` - Sprint is being planned
- `active` - Sprint is currently active
- `completed` - Sprint has finished
- `cancelled` - Sprint was cancelled

## Best Practices

### Development Workflow

To ensure code quality and a smooth development process, we utilize Continuous Integration (CI) and pre-commit hooks.

#### Continuous Integration (CI)

Our CI pipeline automatically runs tests and checks code quality whenever changes are pushed to the repository or a pull request is opened. This helps catch issues early and ensures the codebase remains stable.

- **Automated Testing**: All unit and integration tests are run automatically.
- **Code Quality Checks**: Linters and formatters are executed to enforce coding standards.

#### Pre-Commit Hooks

Pre-commit hooks are scripts that run automatically before each commit. They help maintain code quality by catching simple issues like formatting errors or linting violations before they are committed to the repository.

To install and use pre-commit hooks, navigate to the project root and run:

```bash
pre-commit install
```

This will set up the hooks to run automatically on `git commit`. If any checks fail, the commit will be aborted, allowing you to fix the issues before committing.



### 1. Story Writing
- Use clear, descriptive names
- Write detailed descriptions explaining the "what" and "why"
- Add relevant tags for easy filtering
- Estimate with story points for planning

### 2. Sprint Planning
- Set clear sprint goals
- Don't overcommit - better to under-promise and over-deliver
- Keep sprint duration consistent (e.g., 2 weeks)
- Review and adjust based on team velocity

### 3. Daily Stand-ups
- Check active sprint: `get_active_sprint`
- Review story progress: `list_stories status:"in_progress"`
- Update story statuses as needed
- Identify and mark blocked stories

### 4. Sprint Review
- Check progress: `get_sprint_progress`
- Complete finished stories: `update_story status:"done"`
- Move unfinished stories to next sprint
- Complete the sprint: `update_sprint status:"completed"`

## Common Workflows

### Starting a New Project
1. `set_project` - Set up project directory
2. `create_story` - Add initial stories to backlog
3. `create_sprint` - Create your first sprint
4. `manage_sprint_stories` - Add stories to sprint
5. `update_sprint` - Set sprint to active

### Daily Development
1. `get_active_sprint` - Check current sprint
2. `list_stories status:"in_progress"` - See what you're working on
3. `update_story` - Update progress as you work
4. `get_sprint_progress` - Track overall progress

### Sprint Planning
1. `list_stories status:"todo"` - Review backlog
2. `create_sprint` - Create new sprint
3. `manage_sprint_stories action:"add"` - Add selected stories
4. `update_sprint status:"active"` - Start the sprint

### Sprint Review & Retrospective
1. `get_sprint_progress` - Review what was completed
2. `update_story status:"done"` - Mark completed stories
3. `manage_sprint_stories action:"remove"` - Move unfinished stories
4. `update_sprint status:"completed"` - Close the sprint

## Troubleshooting

### Common Issues

**"Project not initialized" Error**
- Run `set_project` first to set up your project directory

**"Story/Sprint not found" Error**
- Double-check the ID - they're case-sensitive
- Use `list_stories` or `list_sprints` to find correct IDs

**Invalid Parameter Values**
- Check the API reference for valid values
- Status values are case-sensitive and specific
- Story points must be Fibonacci numbers

### Getting Help

- Check the API Reference for detailed parameter information
- Use `list_stories` and `list_sprints` to see current state
- Verify project setup with `get_project`

## Tips for Success

1. **Start Small**: Begin with a few simple stories to get familiar
2. **Be Consistent**: Update story statuses regularly
3. **Review Often**: Use progress tracking tools to stay on track
4. **Plan Realistically**: Don't overcommit in sprints
5. **Tag Effectively**: Use tags to organize and filter stories
6. **Document Goals**: Always set clear sprint goals

Happy project managing! 🚀
