#!/usr/bin/env python3
"""Demo: Cross-turn knowledge assistant scenario.

This script demonstrates the agent's ability to:
1. Research a topic and save notes (Turn 1)
2. Recall notes across sessions (Turn 2)
3. Answer follow-up questions using accumulated knowledge (Turn 3)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.llm_client import LLMClient
from agent.tool_registry import ToolRegistry
from agent.runtime import AgentRuntime
from session.manager import SessionManager
from tools.calculator import Calculator
from tools.web_search import WebSearch
from tools.notes import SaveNote, SearchNotes
from tools.summarize import Summarize
from tools.translate import Translate


def setup():
    llm = LLMClient()
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(WebSearch())
    registry.register(SaveNote())
    registry.register(SearchNotes())
    registry.register(Summarize(llm_client=llm))
    registry.register(Translate(llm_client=llm))
    sm = SessionManager()
    runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=10)
    return runtime, sm


def main():
    print("=" * 60)
    print("  Simple Agent Demo - Cross-Session Knowledge Assistant")
    print("=" * 60)

    runtime, sm = setup()

    # Create session
    session = sm.create("demo")
    print("\n[Session] demo")

    # Turn 1: Research
    print("\n" + "-" * 60)
    print("Turn 1: Research")
    print("-" * 60)
    q1 = "请帮我调研一下 Transformer 架构，重点了解注意力机制"
    print(f"User: {q1}\n")
    r1 = runtime.run(session, q1)
    for t in r1.trace:
        if "tool" in t:
            print(f"  [TOOL] {t['tool']}({t.get('args', {})})")
            print(f"    -> {t.get('result', '')[:120]}...")
        elif t.get("action") == "final_answer":
            print(f"  [DONE] Final Answer")
    print(f"\nAgent: {r1.answer}")
    sm.save(session)

    # Turn 2: Follow-up using knowledge
    print("\n" + "-" * 60)
    print("Turn 2: Follow-up (should use saved notes)")
    print("-" * 60)
    q2 = "注意力机制的具体计算公式是什么？请结合之前调研的内容回答"
    print(f"User: {q2}\n")
    r2 = runtime.run(session, q2)
    for t in r2.trace:
        if "tool" in t:
            print(f"  [TOOL] {t['tool']}({t.get('args', {})})")
            print(f"    -> {t.get('result', '')[:120]}...")
        elif t.get("action") == "final_answer":
            print(f"  [DONE] Final Answer")
    print(f"\nAgent: {r2.answer}")
    sm.save(session)

    # Turn 3: Translation task
    print("\n" + "-" * 60)
    print("Turn 3: Translation task")
    print("-" * 60)
    q3 = "帮我把注意力机制的公式说明翻译成英文"
    print(f"User: {q3}\n")
    r3 = runtime.run(session, q3)
    for t in r3.trace:
        if "tool" in t:
            print(f"  [TOOL] {t['tool']}({t.get('args', {})})")
            print(f"    -> {t.get('result', '')[:120]}...")
        elif t.get("action") == "final_answer":
            print(f"  [DONE] Final Answer")
    print(f"\nAgent: {r3.answer}")
    sm.save(session)

    print("\n" + "=" * 60)
    print(f"Demo complete. Session saved with {len(session.notes)} notes.")
    print("=" * 60)


if __name__ == "__main__":
    main()
