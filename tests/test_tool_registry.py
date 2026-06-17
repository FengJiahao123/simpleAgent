import pytest
from agent.tool_registry import ToolRegistry
from tools.base import Tool


class EchoTool(Tool):
    name = "echo"
    description = "Echo back the message."
    parameters = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message to echo"}
        },
        "required": ["message"]
    }
    def execute(self, message: str, **kwargs) -> str:
        return f"Echo: {message}"


class GreetTool(Tool):
    name = "greet"
    description = "Greet someone."
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name to greet"}
        },
        "required": ["name"]
    }
    def execute(self, name: str, **kwargs) -> str:
        return f"Hello, {name}!"


class TestToolRegistry:
    @pytest.fixture
    def registry(self):
        r = ToolRegistry()
        r.register(EchoTool())
        r.register(GreetTool())
        return r

    def test_register_and_get_definitions(self, registry):
        defs = registry.get_definitions()
        assert len(defs) == 2
        names = [d["function"]["name"] for d in defs]
        assert "echo" in names
        assert "greet" in names

    def test_definition_format(self, registry):
        defs = registry.get_definitions()
        echo_def = [d for d in defs if d["function"]["name"] == "echo"][0]
        assert echo_def["type"] == "function"
        assert "parameters" in echo_def["function"]
        assert echo_def["function"]["parameters"]["type"] == "object"

    def test_execute_registered_tool(self, registry):
        result = registry.execute("echo", {"message": "hello"})
        assert result == "Echo: hello"

    def test_execute_with_extra_kwargs(self, registry):
        """Extra kwargs like session should be passed through."""
        result = registry.execute("greet", {"name": "World"}, session="fake-session")
        assert result == "Hello, World!"

    def test_execute_unknown_tool(self, registry):
        result = registry.execute("unknown_tool", {})
        assert "unknown" in result.lower() or "not found" in result.lower()

    def test_execute_tool_that_raises(self, registry):
        """Tool execution errors should be caught and returned as error strings."""

        class BrokenTool(Tool):
            name = "broken"
            description = "A tool that always fails."
            parameters = {"type": "object", "properties": {}}
            def execute(self, **kwargs) -> str:
                raise RuntimeError("Simulated failure")

        registry.register(BrokenTool())
        result = registry.execute("broken", {})
        assert "error" in result.lower() or "failed" in result.lower()
