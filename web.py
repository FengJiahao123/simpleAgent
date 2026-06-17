#!/usr/bin/env python3
"""Simple Agent — Web UI."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, session as flask_session

from agent.llm_client import LLMClient
from agent.tool_registry import ToolRegistry
from agent.runtime import AgentRuntime
from session.manager import SessionManager
from tools.calculator import Calculator
from tools.web_search import WebSearch
from tools.notes import SaveNote, SearchNotes
from tools.summarize import Summarize
from tools.translate import Translate

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---- Global components ----

llm_client = LLMClient()
registry = ToolRegistry()
registry.register(Calculator())
registry.register(WebSearch())
registry.register(SaveNote())
registry.register(SearchNotes())
registry.register(Summarize(llm_client=llm_client))
registry.register(Translate(llm_client=llm_client))
session_manager = SessionManager()
runtime = AgentRuntime(llm_client=llm_client, tool_registry=registry, max_steps=10)

# Active sessions in memory: {session_id: AgentSession}
active_sessions: dict[str, object] = {}


# ---- Routes ----

@app.route("/")
def index():
    """Serve the chat page."""
    return render_template("index.html")


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    ids = session_manager.list_sessions()
    return jsonify(ids)


@app.route("/api/sessions", methods=["POST"])
def create_session():
    from datetime import datetime
    sid = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    s = session_manager.create(sid)
    session_manager.save(s)
    active_sessions[sid] = s
    return jsonify({"session_id": sid})


@app.route("/api/sessions/<sid>/load", methods=["POST"])
def load_session(sid):
    try:
        s = session_manager.load(sid)
    except FileNotFoundError:
        return jsonify({"error": f"Session '{sid}' not found"}), 404
    active_sessions[sid] = s
    return jsonify({
        "session_id": sid,
        "message_count": len(s.messages),
        "notes_count": len(s.notes),
        "messages": s.messages[-20:],  # last 20 for display
        "notes": [
            {"id": n.id, "content": n.content[:100], "tags": n.tags}
            for n in s.notes
        ],
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    sid = data.get("session_id", "")
    user_input = data.get("message", "").strip()

    if not sid or not user_input:
        return jsonify({"error": "session_id and message required"}), 400

    # Load or use active session
    if sid not in active_sessions:
        try:
            active_sessions[sid] = session_manager.load(sid)
        except FileNotFoundError:
            active_sessions[sid] = session_manager.create(sid)

    session = active_sessions[sid]

    # Run agent
    result = runtime.run(session, user_input)

    # Save after each turn
    session_manager.save(session)

    return jsonify({
        "answer": result.answer,
        "steps": result.steps,
        "trace": [
            {
                "step": t.get("step"),
                "tool": t.get("tool", ""),
                "args": t.get("args", {}),
                "result": t.get("result", "")[:150],
            }
            for t in result.trace
        ],
    })


@app.route("/api/notes/<sid>", methods=["GET"])
def get_notes(sid):
    if sid not in active_sessions:
        try:
            active_sessions[sid] = session_manager.load(sid)
        except FileNotFoundError:
            return jsonify([])
    s = active_sessions[sid]
    return jsonify([
        {"id": n.id, "content": n.content, "tags": n.tags, "created_at": n.created_at}
        for n in s.notes
    ])


if __name__ == "__main__":
    print("=" * 50)
    print("  Simple Agent Web UI")
    print("  Open http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="127.0.0.1", port=5000)
