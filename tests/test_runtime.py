import json
import pytest
from agent.runtime import AgentRuntime, AgentResult
from agent.tool_registry import ToolRegistry
from tools.base import Session, Note


# ---- Fake LLM for testing ----

class FakeLLM:
    """Fake LLM that returns pre-programmed responses for testing the runtime loop."""

    def __init__(self, responses: list):
        self.responses = responses
        self.call_count = 0
        self.call_history = []

    def chat(self, messages, tools=None):
        self.call_history.append({"messages": messages, "tools": tools})
        if self.call_count >= len(self.responses):
            return _make_llm_response(content="I don't know what to do next.")
        resp = self.responses[self.call_count]
        self.call_count += 1
        if isinstance(resp, str):
            return _make_llm_response(content=resp)
        elif isinstance(resp, dict) and "tool_calls" in resp:
            return _make_llm_response(tool_calls=resp["tool_calls"])


def _make_llm_response(content=None, tool_calls=None):
    """Helper to create a fake LLM response matching openai types."""
    class Function:
        def __init__(self, name="", arguments="{}"):
            self.name = name
            self.arguments = arguments

    class ToolCall:
        def __init__(self, id="", function=None):
            self.id = id
            self.function = function

    class Message:
        pass

    msg = Message()
    msg.content = content
    msg.tool_calls = tool_calls
    return msg


def _make_tool_call(name, args):
    """Helper to create a fake tool call."""
    class Function:
        pass

    class ToolCall:
        pass

    tc = ToolCall()
    tc.id = f"call_{name}_001"
    fn = Function()
    fn.name = name
    fn.arguments = args
    tc.function = fn
    return tc


# ---- Tests ----

class TestAgentRuntime:
    @pytest.fixture
    def registry(self):
        r = ToolRegistry()
        from tools.calculator import Calculator
        from tools.web_search import WebSearch
        from tools.notes import SaveNote, SearchNotes
        r.register(Calculator())
        r.register(WebSearch())
        r.register(SaveNote())
        r.register(SearchNotes())
        return r

    @pytest.fixture
    def session(self):
        return Session(session_id="test-runtime")

    def test_direct_answer_no_tools(self, registry, session):
        """When LLM responds with content and no tool calls, return directly."""
        llm = FakeLLM(["The answer is 42."])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry)

        result = runtime.run(session, "What is the answer?")

        assert isinstance(result, AgentResult)
        assert "42" in result.answer
        assert result.steps == 1

    def test_single_tool_call_then_answer(self, registry, session):
        """LLM calls one tool, runtime executes it, LLM gives final answer."""
        tc = _make_tool_call("calculator", '{"expression": "2 + 2"}')
        llm = FakeLLM([
            {"tool_calls": [tc]},
            "2 + 2 equals 4.",
        ])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=5)

        result = runtime.run(session, "Calculate 2+2")

        assert result.steps == 2
        assert "4" in result.answer
        assert len(result.trace) >= 1
        assert result.trace[0]["tool"] == "calculator"

    def test_multi_tool_calls(self, registry, session):
        """LLM calls two tools sequentially before answering."""
        tc1 = _make_tool_call("web_search", '{"query": "Python"}')
        tc2 = _make_tool_call("calculator", '{"expression": "1+1"}')
        llm = FakeLLM([
            {"tool_calls": [tc1]},
            {"tool_calls": [tc2]},
            "Python is a language and 1+1=2.",
        ])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=5)

        result = runtime.run(session, "Tell me about Python and calculate 1+1")

        assert result.steps == 3
        assert len(result.trace) == 3  # 2 tool calls + 1 final answer

    def test_max_steps_limit(self, registry, session):
        """When max_steps is reached, force a final answer."""
        tc = _make_tool_call("calculator", '{"expression": "1+1"}')
        responses = [{"tool_calls": [tc]}] * 10
        llm = FakeLLM(responses)
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=3)

        result = runtime.run(session, "Calculate repeatedly")

        assert result.steps <= 3
        assert len(result.answer) > 0

    def test_tool_error_is_fed_back(self, registry, session):
        """When a tool fails, the error is returned as observation so LLM can adjust."""
        tc = _make_tool_call("calculator", '{"expression": "invalid!!!"}')
        llm = FakeLLM([
            {"tool_calls": [tc]},
            "The calculation failed. Let me try differently: the answer is unknown.",
        ])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=5)

        result = runtime.run(session, "Calculate something broken")

        assert result.steps >= 2

    def test_knowledge_injection(self, registry, session):
        """Related notes should appear in the system prompt."""
        session.notes = [Note(content="Python was created by Guido van Rossum.", tags=["programming"])]

        llm = FakeLLM(["Python was created by Guido van Rossum."])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry)

        result = runtime.run(session, "Who created Python?")
        assert "Guido" in result.answer

        first_messages = llm.call_history[0]["messages"]
        system_msg = first_messages[0]["content"]
        assert "Guido" in system_msg

    def test_session_messages_appended(self, registry, session):
        """After running, session.messages should include user input and assistant response."""
        llm = FakeLLM(["Hello, human!"])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry)

        result = runtime.run(session, "Hi")

        assert len(session.messages) >= 2
        user_msgs = [m for m in session.messages if m["role"] == "user"]
        assert any("Hi" in m["content"] for m in user_msgs)


class TestAgentResult:
    def test_agent_result_fields(self):
        result = AgentResult(
            answer="The answer",
            trace=[{"tool": "test"}],
            total_tokens=100,
            steps=3,
        )
        assert result.answer == "The answer"
        assert len(result.trace) == 1
        assert result.total_tokens == 100
        assert result.steps == 3
