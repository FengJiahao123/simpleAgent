#!/usr/bin/env python3
"""Simple Agent — Web UI."""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_from_directory

from agent.llm_client import LLMClient
from agent.tool_registry import ToolRegistry
from agent.runtime import AgentRuntime
from session.manager import SessionManager
from tools.base import Session
from tools.calculator import Calculator
from tools.web_search import WebSearch
from tools.notes import SaveNote, SearchNotes, export_all_notes_to_md, NOTES_DIR
from tools.summarize import Summarize
from tools.translate import Translate
from tools.export_doc import ExportDoc

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---- Global components ----

try:
    llm_client = LLMClient()
except ValueError as e:
    print(f"[ERROR] {e}")
    print("   Create a .env file in the project root with: DEEPSEEK_API_KEY=sk-...")
    import sys
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

active_sessions: dict[str, Session] = {}


# ---- Page Routes ----

@app.route("/")
def index():
    """Chat page."""
    return render_template("index.html")


@app.route("/notes/<sid>")
def notes_page(sid):
    """Standalone notes viewer page."""
    return render_template("notes.html", session_id=sid)


@app.route("/notes-files/<path:filepath>")
def serve_note_file(filepath):
    """Serve raw .md note files."""
    return send_from_directory(NOTES_DIR, filepath)


# ---- API Routes ----

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
        "messages": s.messages[-30:],
        "notes": [
            {"id": n.id, "content": n.content, "tags": n.tags, "created_at": n.created_at,
             "source_url": n.source_url}
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

    if sid not in active_sessions:
        try:
            active_sessions[sid] = session_manager.load(sid)
        except FileNotFoundError:
            active_sessions[sid] = session_manager.create(sid)

    session = active_sessions[sid]
    result = runtime.run(session, user_input)
    session_manager.save(session)

    # Export notes to .md after each turn
    try:
        export_all_notes_to_md(session)
    except Exception:
        pass

    return jsonify({
        "answer": result.answer,
        "steps": result.steps,
        "trace": [
            {
                "step": t.get("step"),
                "tool": t.get("tool", ""),
                "args": t.get("args", {}),
                "result": t.get("result", ""),
                "action": t.get("action", ""),
                "content": t.get("content", ""),
                "error": t.get("error", ""),
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
        {
            "id": n.id,
            "content": n.content,
            "tags": n.tags,
            "created_at": n.created_at,
            "source_url": n.source_url
        }
        for n in s.notes
    ])


@app.route("/api/notes/<sid>/files", methods=["GET"])
def list_note_files(sid):
    """List .md note files for a session."""
    notes_path = os.path.join(NOTES_DIR, sid)
    if not os.path.exists(notes_path):
        return jsonify([])
    files = sorted(os.listdir(notes_path))
    return jsonify([f for f in files if f.endswith(".md")])


if __name__ == "__main__":
    print("=" * 60)
    print("  Simple Agent Web UI")
    print("  Chat:   http://127.0.0.1:5000")
    print("  Notes:  http://127.0.0.1:5000/notes/<session_id>")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
