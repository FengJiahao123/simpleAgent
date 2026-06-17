from tools.base import Tool


class ToolRegistry:
    """Manages tool registration, definition generation, and execution."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool

    def get_definitions(self) -> list[dict]:
        """Generate function calling definitions for all registered tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, args: dict, **extra) -> str:
        """Execute a tool by name with the given arguments.
        Extra keyword arguments (e.g. session) are passed through to the tool.
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: Unknown tool '{name}'. Available tools: {', '.join(self._tools.keys())}"

        try:
            return tool.execute(**args, **extra)
        except Exception as e:
            return f"Error executing tool '{name}': {e}"
