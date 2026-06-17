"""Integration test: full agent pipeline with fake LLM."""
import os
import sys
import pytest
from agent.tool_registry import ToolRegistry
from agent.runtime import AgentRuntime
from session.manager import SessionManager
from tools.calculator import Calculator
from tools.web_search import WebSearch
from tools.notes import SaveNote, SearchNotes
from tools.summarize import Summarize
from tools.translate import Translate

# Reuse the FakeLLM helpers from test_runtime
sys.path.insert(0, ".")
from tests.test_runtime import FakeLLM, _make_tool_call


class TestIntegration:
    @pytest.fixture
    def components(self):
        registry = ToolRegistry()
        registry.register(Calculator())
        registry.register(WebSearch())
        registry.register(SaveNote())
        registry.register(SearchNotes())

        fake_llm = FakeLLM([])
        registry.register(Summarize(llm_client=fake_llm))
        registry.register(Translate(llm_client=fake_llm))

        session_manager = SessionManager()

        return registry, session_manager

    def test_research_workflow(self, components):
        """Simulate a complete research workflow."""
        registry, session_manager = components
        session = session_manager.create("integration-test")

        tc1 = _make_tool_call("web_search", '{"query": "Transformer architecture"}')
        tc2 = _make_tool_call("save_note", '{"content": "Transformer uses self-attention.", "tags": ["AI", "NLP"]}')
        llm = FakeLLM([
            {"tool_calls": [tc1]},
            {"tool_calls": [tc2]},
            "I've researched Transformer architecture and saved the key findings as a note.",
        ])

        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=5)
        result = runtime.run(session, "Research Transformer architecture")

        assert result.steps == 3
        assert len(result.trace) == 3
        assert len(session.notes) == 1
        assert "self-attention" in session.notes[0].content.lower()

    def test_cross_turn_continuity(self, components):
        """Test cross-turn continuity: Turn 1 researches, Turn 2 recalls.

        Turn 1: Research and save notes.
        Turn 2: Follow-up question — notes should be injected into system prompt.
        """
        registry, session_manager = components
        session = session_manager.create("cross-turn")

        # Turn 1: Research Transformer
        tc1 = _make_tool_call("web_search", '{"query": "Transformer"}')
        tc2 = _make_tool_call(
            "save_note",
            '{"content": "Transformer uses self-attention.", "tags": ["AI"]}',
        )
        llm1 = FakeLLM([
            {"tool_calls": [tc1]},
            {"tool_calls": [tc2]},
            "Saved note about Transformer.",
        ])
        runtime1 = AgentRuntime(llm_client=llm1, tool_registry=registry, max_steps=5)
        result1 = runtime1.run(session, "Research Transformer")
        assert len(session.notes) == 1

        # Save and reload to simulate program restart
        session_manager.save(session)
        loaded_session = session_manager.load("cross-turn")
        assert len(loaded_session.notes) == 1

        # Turn 2: Follow-up question
        llm2 = FakeLLM([
            "Based on your previous research, Transformer uses self-attention mechanism."
        ])
        runtime2 = AgentRuntime(llm_client=llm2, tool_registry=registry, max_steps=5)
        result2 = runtime2.run(loaded_session, "What mechanism does Transformer use?")

        # The note should have been injected into the system prompt
        first_call = llm2.call_history[0]
        system_prompt = first_call["messages"][0]["content"]
        assert "self-attention" in system_prompt.lower()

        # Cleanup
        os.remove(session_manager._filepath("cross-turn"))
