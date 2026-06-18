#!/usr/bin/env python3
"""Simple Agent — A personal knowledge base assistant.

Usage:
    python main.py                  # Interactive mode (creates or resumes session)
    python main.py new              # Create a new session
    python main.py resume <id>      # Resume an existing session
    python main.py list             # List all sessions
    python main.py delete <id>      # Delete a session
"""

import os
import sys
import signal
from session.manager import SessionManager


def print_trace(trace: list[dict], max_steps: int):
    """Print formatted trace of agent execution."""
    for entry in trace:
        step = entry.get("step", "?")
        if "tool" in entry:
            args_str = ", ".join(f"{k}={v}" for k, v in entry.get("args", {}).items())
            print(f"  [Step {step}/{max_steps}] [TOOL] {entry['tool']}({args_str})")
            result = entry.get("result", "")
            if len(result) > 100:
                result = result[:100] + "..."
            print(f"    -> {result}")
        elif entry.get("action") == "final_answer":
            print(f"  [Step {step}/{max_steps}] [DONE] Final Answer")
        elif "error" in entry:
            print(f"  [Step {step}/{max_steps}] [ERROR] {entry['error']}")


def build_runtime():
    """Wire up all components (requires DEEPSEEK_API_KEY)."""
    from agent.llm_client import LLMClient
    from agent.tool_registry import ToolRegistry
    from agent.runtime import AgentRuntime
    from tools.calculator import Calculator
    from tools.web_search import WebSearch
    from tools.notes import SaveNote, SearchNotes
    from tools.summarize import Summarize
    from tools.translate import Translate
    from tools.export_doc import ExportDoc

    try:
        llm_client = LLMClient()
    except ValueError as e:
        print(f"[ERROR] Configuration Error: {e}")
        print("   Set DEEPSEEK_API_KEY environment variable to your DeepSeek API key.")
        print("   Example: export DEEPSEEK_API_KEY=sk-...")
        sys.exit(1)

    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(WebSearch())
    registry.register(SaveNote())
    registry.register(SearchNotes())
    registry.register(Summarize(llm_client=llm_client))
    registry.register(Translate(llm_client=llm_client))
    registry.register(ExportDoc())

    session_manager = SessionManager()
    runtime = AgentRuntime(llm_client=llm_client, tool_registry=registry, max_steps=10)

    return runtime, session_manager


def interactive_loop(runtime, session_manager: SessionManager):
    """Main interactive loop."""
    sessions = session_manager.list_sessions()
    if sessions:
        print("[Sessions] Existing sessions:")
        for s in sessions:
            print(f"   * {s}")
        print()
        choice = input("Enter session ID to resume, or press Enter for new: ").strip()
    else:
        choice = ""

    if choice:
        session_id = choice
        try:
            session = session_manager.load(session_id)
            print(f"[Sessions] Resumed session: {session_id}")
            print(f"   {len(session.messages)} messages, {len(session.notes)} notes loaded.\n")
        except FileNotFoundError:
            print(f"Session '{session_id}' not found. Creating new session.")
            session = session_manager.create(session_id)
    else:
        from datetime import datetime
        session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        session = session_manager.create(session_id)
        print(f"[Sessions] Created new session: {session_id}\n")

    def save_on_exit(*args):
        print("\n[Saving] Saving session...")
        session_manager.save(session)
        print(f"[Done] Session saved to data/sessions/{session_id}.json")
        print("Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, save_on_exit)

    print("Simple Agent is ready. Type 'exit' to quit, 'notes' to see your notes.\n")

    while True:
        try:
            user_input = input("Agent > ").strip()
        except (EOFError, KeyboardInterrupt):
            save_on_exit()
            return

        if not user_input:
            continue

        if user_input.lower() == "exit":
            save_on_exit()
            return

        if user_input.lower() == "notes":
            if session.notes:
                print(f"[Notes] You have {len(session.notes)} note(s):")
                for i, note in enumerate(session.notes, 1):
                    tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
                    print(f"   {i}.{tags_str} {note.content[:100]}...")
            else:
                print("[Notes] No notes yet. Ask me to research something!")
            print()
            continue

        print()
        result = runtime.run(session, user_input)
        print_trace(result.trace, runtime.max_steps)
        print(f"\n{result.answer}\n")
        print(f"   ({result.steps} step(s))\n")

        session_manager.save(session)


def main():
    args = sys.argv[1:]

    # Commands that don't need LLM
    if args:
        command = args[0].lower()

        if command == "list":
            sm = SessionManager()
            sessions = sm.list_sessions()
            if sessions:
                print(f"[Sessions] {len(sessions)} session(s):")
                for s in sessions:
                    print(f"   * {s}")
            else:
                print("[Sessions] No sessions found. Create one with: python main.py new")
            return

        if command == "new":
            from datetime import datetime
            sm = SessionManager()
            session_id = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            session = sm.create(session_id)
            sm.save(session)
            print(f"[Done] Created new session: {session_id}")
            print(f"   Run: python main.py resume {session_id}")
            return

        if command == "delete":
            if len(args) < 2:
                print("Usage: python main.py delete <session_id>")
                return
            session_id = args[1]
            filepath = os.path.join("data", "sessions", f"{session_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"[Done] Deleted session: {session_id}")
            else:
                print(f"[Error] Session '{session_id}' not found.")
            return

    # Commands that need LLM
    runtime, session_manager = build_runtime()

    if not args:
        interactive_loop(runtime, session_manager)
        return

    command = args[0].lower()

    if command == "resume":
        if len(args) < 2:
            print("Usage: python main.py resume <session_id>")
            return
        session_id = args[1]
        try:
            session = session_manager.load(session_id)
        except FileNotFoundError:
            print(f"[Error] Session '{session_id}' not found.")
            return

        print(f"[Sessions] Resumed session: {session_id}")
        print(f"   {len(session.messages)} messages, {len(session.notes)} notes.")
        print("   Entering interactive mode...\n")

        def save_on_exit(*args):
            print("\n[Saving] Saving...")
            session_manager.save(session)
            print("Goodbye!")
            sys.exit(0)

        signal.signal(signal.SIGINT, save_on_exit)

        while True:
            try:
                user_input = input("Agent > ").strip()
            except (EOFError, KeyboardInterrupt):
                save_on_exit()
                return
            if not user_input:
                continue
            if user_input.lower() == "exit":
                save_on_exit()
                return
            print()
            result = runtime.run(session, user_input)
            print_trace(result.trace, runtime.max_steps)
            print(f"\n{result.answer}\n")
            print(f"   ({result.steps} step(s))\n")
            session_manager.save(session)

    else:
        print(f"Unknown command: {command}")
        print("Available: new, resume <id>, list, delete <id>")


if __name__ == "__main__":
    main()
