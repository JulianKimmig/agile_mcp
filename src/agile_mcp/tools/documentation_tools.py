"""Documentation tools for Agile MCP Server."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import AgileTool, ToolError


class GetAgileDocumentationTool(AgileTool):
    """Retrieve comprehensive machine-readable agile methodology documentation."""
    
    def apply(self, topic: Optional[str] = None, format: str = "json", detail_level: str = "comprehensive") -> str:
        """Get machine-readable agile methodology documentation.
        
        Args:
            topic: Specific topic to retrieve (optional). Options: "principles", "tools", "workflows", "best_practices", "all"
            format: Output format (optional, default: "json"). Options: "json", "yaml"
            detail_level: Detail level (optional, default: "comprehensive"). Options: "summary", "comprehensive"
            
        Returns:
            Machine-readable agile documentation in requested format
        """
        # Validate parameters
        valid_topics = ["principles", "tools", "workflows", "best_practices", "methodologies", "decision_trees", "all", None]
        if topic not in valid_topics:
            raise ToolError(f"Invalid topic. Must be one of: {[t for t in valid_topics if t is not None]}")
        
        valid_formats = ["json", "yaml"]
        if format not in valid_formats:
            raise ToolError(f"Invalid format. Must be one of: {valid_formats}")
        
        valid_detail_levels = ["summary", "comprehensive"]
        if detail_level not in valid_detail_levels:
            raise ToolError(f"Invalid detail_level. Must be one of: {valid_detail_levels}")
        
        # Generate the documentation
        documentation = self._generate_agile_documentation()
        
        # Filter by topic if specified
        if topic and topic != "all":
            if topic not in documentation:
                raise ToolError(f"Topic '{topic}' not found in documentation")
            documentation = {
                "metadata": documentation["metadata"],
                topic: documentation[topic]
            }
        
        # Adjust detail level
        if detail_level == "summary":
            documentation = self._create_summary_documentation(documentation)
        
        # Format output
        if format == "yaml":
            try:
                import yaml
                output = yaml.dump(documentation, default_flow_style=False, indent=2)
            except ImportError:
                raise ToolError("YAML format requires PyYAML package. Install with: pip install PyYAML")
        else:
            output = json.dumps(documentation, indent=2)
        
        # Store result data for MCP response
        self.last_result_data = {
            "topic": topic or "all",
            "format": format,
            "detail_level": detail_level,
            "documentation": documentation
        }
        
        return f"Agile methodology documentation retrieved successfully. Topic: {topic or 'all'}, Format: {format}, Detail level: {detail_level}. Content length: {len(output)} characters."
    
    def _generate_agile_documentation(self) -> Dict[str, Any]:
        """Generate comprehensive agile methodology documentation."""
        return {
            "metadata": {
                "version": "1.0.0",
                "schema_version": "1.0",
                "created_at": "2025-01-07T12:00:00Z",
                "updated_at": "2025-01-07T12:00:00Z"
            },
            "agile_principles": {
                "manifesto": {
                    "values": [
                        {
                            "primary": "Individuals and interactions",
                            "secondary": "processes and tools",
                            "explanation": "While processes and tools are important, the focus should be on people and how they work together. Communication, collaboration, and human relationships drive successful software development."
                        },
                        {
                            "primary": "Working software",
                            "secondary": "comprehensive documentation",
                            "explanation": "Documentation has value, but working software that delivers value to users is more important. Focus on building functional software that meets user needs."
                        },
                        {
                            "primary": "Customer collaboration",
                            "secondary": "contract negotiation",
                            "explanation": "While contracts define scope and expectations, ongoing collaboration with customers ensures the product meets their evolving needs and provides real value."
                        },
                        {
                            "primary": "Responding to change",
                            "secondary": "following a plan",
                            "explanation": "Plans provide direction, but the ability to adapt and respond to change is more valuable. Embrace change as an opportunity to deliver better solutions."
                        }
                    ],
                    "principles": [
                        {
                            "title": "Satisfy the customer through early and continuous delivery",
                            "description": "Our highest priority is to satisfy the customer through early and continuous delivery of valuable software.",
                            "practical_application": "Implement short development cycles, frequent releases, and regular customer feedback loops."
                        },
                        {
                            "title": "Welcome changing requirements",
                            "description": "Welcome changing requirements, even late in development. Agile processes harness change for the customer's competitive advantage.",
                            "practical_application": "Build flexible systems, maintain open communication channels, and view change requests as opportunities for improvement."
                        },
                        {
                            "title": "Deliver working software frequently",
                            "description": "Deliver working software frequently, from a couple of weeks to a couple of months, with a preference to the shorter timescale.",
                            "practical_application": "Use time-boxed sprints, continuous integration, and incremental delivery to provide regular value."
                        }
                    ]
                }
            },
            "methodologies": {
                "scrum": {
                    "description": "Scrum is an agile framework for developing, delivering, and sustaining complex products through iterative and incremental practices.",
                    "roles": [
                        {
                            "name": "Product Owner",
                            "responsibilities": [
                                "Define and prioritize product backlog",
                                "Communicate vision and requirements",
                                "Accept or reject work results",
                                "Represent stakeholder interests"
                            ],
                            "interactions": [
                                "Works closely with development team on clarifications",
                                "Collaborates with stakeholders on requirements",
                                "Partners with Scrum Master on process optimization"
                            ]
                        },
                        {
                            "name": "Scrum Master",
                            "responsibilities": [
                                "Facilitate Scrum events",
                                "Remove impediments",
                                "Coach team on Scrum practices",
                                "Protect team from external disruptions"
                            ],
                            "interactions": [
                                "Serves the development team as a facilitator",
                                "Helps Product Owner with backlog management",
                                "Works with organization to improve agile adoption"
                            ]
                        },
                        {
                            "name": "Development Team",
                            "responsibilities": [
                                "Deliver potentially shippable product increment",
                                "Self-organize to accomplish sprint goals",
                                "Collaborate on technical decisions",
                                "Estimate and commit to sprint work"
                            ]
                        }
                    ],
                    "events": [
                        {
                            "name": "Sprint Planning",
                            "purpose": "Define what can be delivered in the sprint and how the work will be achieved",
                            "duration": "2-4 hours for 2-week sprint",
                            "participants": ["Product Owner", "Scrum Master", "Development Team"],
                            "outcomes": ["Sprint goal", "Sprint backlog", "Team commitment"],
                            "tools_used": ["create_sprint", "list_stories", "manage_sprint_stories"]
                        },
                        {
                            "name": "Daily Scrum",
                            "purpose": "Synchronize team activities and plan for the next 24 hours",
                            "duration": "15 minutes",
                            "participants": ["Development Team", "Scrum Master (optional)"],
                            "outcomes": ["Updated task status", "Identified impediments", "Daily plan"],
                            "tools_used": ["get_active_sprint", "list_stories", "update_story"]
                        },
                        {
                            "name": "Sprint Review",
                            "purpose": "Inspect the increment and adapt the product backlog",
                            "duration": "1-2 hours for 2-week sprint",
                            "participants": ["Scrum Team", "Stakeholders"],
                            "outcomes": ["Demonstrated increment", "Updated product backlog", "Stakeholder feedback"],
                            "tools_used": ["get_sprint_progress", "list_stories", "update_story"]
                        },
                        {
                            "name": "Sprint Retrospective",
                            "purpose": "Plan ways to increase quality and effectiveness",
                            "duration": "1-1.5 hours for 2-week sprint",
                            "participants": ["Scrum Team"],
                            "outcomes": ["Process improvements", "Action items", "Team agreements"],
                            "tools_used": ["get_sprint_progress", "update_sprint"]
                        }
                    ],
                    "artifacts": [
                        {
                            "name": "Product Backlog",
                            "description": "Ordered list of features, functions, requirements, enhancements, and fixes",
                            "owner": "Product Owner",
                            "creation_tools": ["create_story", "update_story", "list_stories"]
                        },
                        {
                            "name": "Sprint Backlog",
                            "description": "Set of product backlog items selected for the sprint plus a plan for delivering them",
                            "owner": "Development Team",
                            "creation_tools": ["create_sprint", "manage_sprint_stories"]
                        },
                        {
                            "name": "Increment",
                            "description": "Sum of all product backlog items completed during a sprint and all previous sprints",
                            "owner": "Development Team",
                            "creation_tools": ["update_story", "get_sprint_progress"]
                        }
                    ]
                }
            },
            "workflow_patterns": [
                {
                    "name": "Project Initialization",
                    "description": "Setting up a new agile project from scratch",
                    "context": "When starting a new project or initializing agile practices in an existing project",
                    "steps": [
                        {
                            "sequence": 1,
                            "action": "Set up project directory",
                            "tool": "set_project",
                            "parameters": {"project_path": "."}
                        },
                        {
                            "sequence": 2,
                            "action": "Create initial user stories",
                            "tool": "create_story",
                            "parameters": {"title": "Example Story", "description": "Initial backlog item"}
                        },
                        {
                            "sequence": 3,
                            "action": "Create first sprint",
                            "tool": "create_sprint",
                            "parameters": {"name": "Sprint 1", "goal": "Initial implementation"}
                        }
                    ],
                    "outcomes": ["Initialized project structure", "Basic backlog", "First sprint ready"]
                },
                {
                    "name": "Sprint Planning Workflow",
                    "description": "Complete sprint planning process from backlog review to sprint commitment",
                    "context": "At the beginning of each sprint to plan the work for the upcoming iteration",
                    "steps": [
                        {
                            "sequence": 1,
                            "action": "Review available stories",
                            "tool": "list_stories",
                            "parameters": {"status": "todo"}
                        },
                        {
                            "sequence": 2,
                            "action": "Create new sprint",
                            "tool": "create_sprint",
                            "parameters": {"name": "Sprint X", "goal": "Sprint objective"}
                        },
                        {
                            "sequence": 3,
                            "action": "Add stories to sprint",
                            "tool": "manage_sprint_stories",
                            "parameters": {"action": "add"},
                            "decision_points": [
                                {
                                    "condition": "Story fits in sprint capacity",
                                    "action_if_true": "Add story to sprint",
                                    "action_if_false": "Leave story in backlog for future sprint"
                                }
                            ]
                        },
                        {
                            "sequence": 4,
                            "action": "Activate sprint",
                            "tool": "update_sprint",
                            "parameters": {"status": "active"}
                        }
                    ],
                    "outcomes": ["Active sprint with committed stories", "Clear sprint goal", "Team alignment"]
                }
            ],
            "tools": {
                "categories": [
                    {
                        "name": "Project Management",
                        "description": "Tools for setting up and managing project-level configuration",
                        "tools": [
                            {
                                "name": "set_project",
                                "description": "Set the project directory for agile project management",
                                "parameters": [
                                    {
                                        "name": "project_path",
                                        "type": "string",
                                        "required": True,
                                        "description": "Path to the project directory. Can be relative or absolute. Use '.' for current directory.",
                                        "examples": [".", "/path/to/project", "../my-project"]
                                    }
                                ],
                                "use_cases": [
                                    {
                                        "scenario": "Starting a new agile project",
                                        "example": {"project_path": "."},
                                        "workflow_context": "First step in project initialization workflow"
                                    },
                                    {
                                        "scenario": "Switching between multiple projects",
                                        "example": {"project_path": "/path/to/different/project"},
                                        "workflow_context": "Project context switching for multi-project teams"
                                    }
                                ],
                                "best_practices": [
                                    "Always set project directory before using other tools",
                                    "Use absolute paths for consistency across environments",
                                    "Verify project directory exists and is accessible"
                                ],
                                "common_errors": [
                                    {
                                        "error": "Project path does not exist",
                                        "cause": "Specified directory doesn't exist on filesystem",
                                        "solution": "Create directory first or use existing directory path"
                                    }
                                ],
                                "related_tools": [
                                    {
                                        "tool": "get_project",
                                        "relationship": "complementary - use to verify current project"
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "Story Management",
                        "description": "Tools for creating, updating, and managing user stories",
                        "tools": [
                            {
                                "name": "create_story",
                                "description": "Create a new user story in the agile project",
                                "parameters": [
                                    {
                                        "name": "title",
                                        "type": "string",
                                        "required": True,
                                        "description": "Story title - should be concise and descriptive",
                                        "examples": ["User Authentication", "Payment Processing", "Data Export Feature"]
                                    },
                                    {
                                        "name": "description",
                                        "type": "string",
                                        "required": True,
                                        "description": "Detailed story description explaining what and why",
                                        "examples": ["As a user, I want to log in securely so that I can access my account"]
                                    },
                                    {
                                        "name": "priority",
                                        "type": "string",
                                        "required": False,
                                        "description": "Story priority level",
                                        "examples": ["low", "medium", "high", "critical"]
                                    }
                                ],
                                "use_cases": [
                                    {
                                        "scenario": "Capturing new requirements from stakeholders",
                                        "example": {
                                            "title": "User Profile Management",
                                            "description": "As a user, I want to update my profile information so that my account details stay current",
                                            "priority": "medium"
                                        },
                                        "workflow_context": "Backlog building and requirement capture"
                                    }
                                ],
                                "best_practices": [
                                    "Write stories from user perspective using 'As a... I want... So that...' format",
                                    "Keep stories small and focused on single functionality",
                                    "Include acceptance criteria in description when possible"
                                ]
                            }
                        ]
                    }
                ]
            },
            "best_practices": {
                "story_writing": [
                    {
                        "principle": "User-focused perspective",
                        "explanation": "Write stories from the end user's point of view to maintain focus on value delivery",
                        "examples": [
                            {
                                "good": "As a customer, I want to track my order status so that I know when to expect delivery",
                                "bad": "Implement order tracking system",
                                "why": "The good example explains who benefits and why, while the bad example is just a technical task"
                            }
                        ]
                    },
                    {
                        "principle": "Independent and negotiable",
                        "explanation": "Stories should be able to be developed independently and details should be negotiable",
                        "examples": [
                            {
                                "good": "User can reset password via email",
                                "bad": "User can reset password via email and SMS and security questions",
                                "why": "The good example is focused and can be implemented independently, while the bad example bundles multiple features"
                            }
                        ]
                    }
                ],
                "sprint_planning": [
                    {
                        "practice": "Capacity-based planning",
                        "description": "Plan sprints based on team capacity and historical velocity, not wishful thinking",
                        "tools_involved": ["list_stories", "create_sprint", "manage_sprint_stories"],
                        "metrics": ["Team velocity", "Story points", "Historical completion rates"]
                    },
                    {
                        "practice": "Clear sprint goals",
                        "description": "Each sprint should have a clear, achievable goal that provides focus and direction",
                        "tools_involved": ["create_sprint", "update_sprint"],
                        "metrics": ["Goal achievement rate", "Scope changes during sprint"]
                    }
                ],
                "estimation": {
                    "techniques": [
                        {
                            "name": "Planning Poker",
                            "description": "Team-based estimation using Fibonacci sequence for relative sizing",
                            "when_to_use": "When team has diverse perspectives and you want consensus",
                            "implementation": "Use story points with Fibonacci scale (1, 2, 3, 5, 8, 13, 21)"
                        },
                        {
                            "name": "T-shirt sizing",
                            "description": "High-level estimation using size categories (XS, S, M, L, XL)",
                            "when_to_use": "For initial rough estimation or large number of items",
                            "implementation": "Map sizes to story points later for sprint planning"
                        }
                    ],
                    "story_points": {
                        "scale": [
                            {
                                "value": 1,
                                "meaning": "Very small, simple task",
                                "typical_tasks": ["Minor bug fix", "Simple configuration change", "Documentation update"]
                            },
                            {
                                "value": 2,
                                "meaning": "Small task with some complexity",
                                "typical_tasks": ["Simple feature addition", "Basic UI component", "Simple API endpoint"]
                            },
                            {
                                "value": 3,
                                "meaning": "Medium task with moderate complexity",
                                "typical_tasks": ["Feature with business logic", "Database schema changes", "Integration with external service"]
                            },
                            {
                                "value": 5,
                                "meaning": "Larger task requiring significant work",
                                "typical_tasks": ["Complex feature development", "Major refactoring", "Multi-component integration"]
                            },
                            {
                                "value": 8,
                                "meaning": "Large task with high complexity",
                                "typical_tasks": ["Major feature with multiple components", "Complex algorithm implementation", "Significant architectural changes"]
                            }
                        ],
                        "guidelines": [
                            "Use relative sizing - compare stories to each other, not absolute time",
                            "Consider complexity, uncertainty, and effort in estimation",
                            "Stories larger than 8 points should be broken down into smaller stories",
                            "Re-estimate stories if new information changes understanding"
                        ]
                    }
                }
            },
            "decision_trees": [
                {
                    "name": "Tool Selection for Story Management",
                    "purpose": "Help decide which tool to use for different story management scenarios",
                    "root_question": "What do you want to do with stories?",
                    "nodes": [
                        {
                            "id": "root",
                            "question": "What story operation do you need?",
                            "options": [
                                {
                                    "condition": "Create new story",
                                    "next_node": "create_story_node",
                                    "tools": ["create_story"]
                                },
                                {
                                    "condition": "Find existing stories",
                                    "next_node": "find_stories_node",
                                    "tools": ["list_stories", "get_story"]
                                },
                                {
                                    "condition": "Modify existing story",
                                    "next_node": "modify_story_node",
                                    "tools": ["update_story"]
                                },
                                {
                                    "condition": "Remove story",
                                    "next_node": "END",
                                    "action": "Use delete_story tool",
                                    "tools": ["delete_story"]
                                }
                            ]
                        },
                        {
                            "id": "create_story_node",
                            "question": "Do you have all story details ready?",
                            "options": [
                                {
                                    "condition": "Yes, I have title, description, and priority",
                                    "next_node": "END",
                                    "action": "Use create_story with all parameters",
                                    "tools": ["create_story"]
                                },
                                {
                                    "condition": "Only have basic information",
                                    "next_node": "END",
                                    "action": "Use create_story with minimal parameters, update later",
                                    "tools": ["create_story", "update_story"]
                                }
                            ]
                        },
                        {
                            "id": "find_stories_node",
                            "question": "Do you know the specific story ID?",
                            "options": [
                                {
                                    "condition": "Yes, I have the story ID",
                                    "next_node": "END",
                                    "action": "Use get_story with story_id",
                                    "tools": ["get_story"]
                                },
                                {
                                    "condition": "No, I need to search or filter",
                                    "next_node": "END",
                                    "action": "Use list_stories with appropriate filters",
                                    "tools": ["list_stories"]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def _create_summary_documentation(self, documentation: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summarized version of the documentation."""
        summary = {
            "metadata": documentation["metadata"],
        }
        
        # Add summarized sections
        if "agile_principles" in documentation:
            summary["agile_principles"] = {
                "manifesto": {
                    "values_count": len(documentation["agile_principles"]["manifesto"]["values"]),
                    "principles_count": len(documentation["agile_principles"]["manifesto"]["principles"])
                }
            }
        
        if "methodologies" in documentation:
            summary["methodologies"] = {}
            for method_name, method_data in documentation["methodologies"].items():
                summary["methodologies"][method_name] = {
                    "description": method_data.get("description", ""),
                    "roles_count": len(method_data.get("roles", [])),
                    "events_count": len(method_data.get("events", [])),
                    "artifacts_count": len(method_data.get("artifacts", []))
                }
        
        if "workflow_patterns" in documentation:
            summary["workflow_patterns"] = [
                {
                    "name": pattern["name"],
                    "description": pattern["description"],
                    "steps_count": len(pattern["steps"])
                }
                for pattern in documentation["workflow_patterns"]
            ]
        
        if "tools" in documentation:
            summary["tools"] = {
                "categories_count": len(documentation["tools"]["categories"]),
                "total_tools": sum(len(cat["tools"]) for cat in documentation["tools"]["categories"])
            }
        
        return summary
    
    def apply_with_error_handling(self, **kwargs: Any):
        """Override to include data in result."""
        result = super().apply_with_error_handling(**kwargs)
        if result.success and hasattr(self, 'last_result_data'):
            result.data = self.last_result_data
            delattr(self, 'last_result_data')
        return result 