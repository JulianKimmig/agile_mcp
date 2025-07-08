"""Burndown chart tool for Agile MCP Server."""

from .base import AgileTool, ToolError, ToolResult
from ..services.sprint_service import SprintService
from ..storage.filesystem import AgileProjectManager


class GetSprintBurndownChartTool(AgileTool):
    """Get a burndown chart for a specific sprint."""

    def apply(self, sprint_id: str) -> ToolResult:
        """Get a burndown chart for a specific sprint.

        Args:
            sprint_id: The ID of the sprint to get the burndown chart for (required)

        Returns:
            A string representation of the burndown chart
        """
        self._check_project_initialized()

        sprint_service = SprintService(self.agent.project_manager)
        burndown_data = sprint_service.get_sprint_burndown_data(sprint_id)

        if burndown_data is None or not burndown_data or not self._has_required_keys(burndown_data):
            raise ToolError(f"Could not generate burndown chart for sprint with ID {sprint_id}")

        chart_text = self._generate_chart(burndown_data)
        
        return self.format_result(
            f"Generated burndown chart for sprint: {burndown_data['sprint_name']}",
            {
                "sprint_id": sprint_id,
                "sprint_name": burndown_data["sprint_name"],
                "chart": chart_text,
                "burndown_data": burndown_data
            }
        )

    def _has_required_keys(self, data: dict) -> bool:
        """Check if the data contains all required keys for chart generation."""
        required_keys = ["sprint_name", "ideal_burn_per_day", "burndown"]
        return all(key in data for key in required_keys)

    def _generate_chart(self, data: dict) -> str:
        """Generates a textual burndown chart."""
        chart = []
        chart.append(f"Burndown Chart for Sprint: {data['sprint_name']}\n")
        chart.append(f"Ideal Burn: {data['ideal_burn_per_day']:.2f} points/day\n")
        chart.append("Date        | Remaining Points | Ideal Burn")
        chart.append("------------|------------------|-----------")

        for entry in data["burndown"]:
            date = entry["date"]
            remaining = entry["remaining_points"]
            ideal = entry["ideal_points"]
            chart.append(f"{date} | {remaining:<16} | {ideal:.2f}")

        return "\n".join(chart)
