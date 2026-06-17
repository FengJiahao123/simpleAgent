import pytest
from tools.base import Tool


class FakeTool(Tool):
    name = "fake_tool"
    description = "A fake tool for testing"
    parameters = {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "First argument"}
        },
        "required": ["arg1"]
    }

    def execute(self, arg1: str, **kwargs) -> str:
        return f"executed with {arg1}"


class TestTool:
    def test_tool_must_implement_execute(self):
        """Tool is abstract — cannot instantiate without implementing execute()."""
        with pytest.raises(TypeError):
            Tool()  # type: ignore

    def test_tool_execute_returns_string(self):
        tool = FakeTool()
        result = tool.execute(arg1="hello")
        assert result == "executed with hello"
        assert isinstance(result, str)

    def test_tool_has_required_attributes(self):
        tool = FakeTool()
        assert tool.name == "fake_tool"
        assert "fake" in tool.description
        assert "properties" in tool.parameters
        assert "arg1" in tool.parameters["properties"]

    def test_tool_extra_kwargs_are_silently_ignored(self):
        """Tools should accept extra kwargs (e.g. session) without error."""
        tool = FakeTool()
        result = tool.execute(arg1="test", session=None, _context={})
        assert result == "executed with test"
