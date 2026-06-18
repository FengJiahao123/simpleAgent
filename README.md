# Simple Agent — Personal Knowledge Base Assistant

A minimal usable Agent built from scratch — no LangChain, no Agent frameworks. Core runtime implemented by hand.

## Quick Start

### 1. Setup

```bash
# Python 3.10+
pip install -r requirements.txt
```

### 2. API Key

```bash
# Get your API key from https://platform.deepseek.com
export DEEPSEEK_API_KEY="sk-your-deepseek-api-key"

# Optional: custom base URL
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
```

### 3. Run

```bash
# Interactive mode (auto-create or select session)
python main.py

# Create new session
python main.py new

# Resume session
python main.py resume <session_id>

# List all sessions
python main.py list

# Delete session
python main.py delete <session_id>

# Run demo
python demo.py
```

### 4. Test

```bash
pytest tests/ -v
```

## System Design

### Architecture

```
CLI (main.py)
    |
    v
Agent Runtime (agent/runtime.py)
    +-- LLM Client (agent/llm_client.py) -> DeepSeek API
    +-- Tool Registry (agent/tool_registry.py)
    |   +-- Calculator (tools/calculator.py)
    |   +-- WebSearch (tools/web_search.py)   [real search via Baidu]
    |   +-- SaveNote / SearchNotes (tools/notes.py)
    |   +-- Summarize (tools/summarize.py)
    |   +-- Translate (tools/translate.py)
    |   +-- ExportDoc (tools/export_doc.py)
    +-- Session Manager (session/manager.py)
        +-- data/sessions/<id>.json
```

### Agent Main Loop (ReAct-style)

```
User Input
  -> Build System Prompt (inject relevant knowledge notes)
  -> LLM analyzes (direct answer? or call tool?)
  -> Has tool_calls -> ToolRegistry executes tool -> result goes back to messages
  -> Back to LLM (with tool results)
  -> No tool_calls -> Final answer
  -> Return answer + Trace log
```

- **Max steps**: 10 (prevents infinite loops)
- **LLM retry**: 2 retries on API failure (1s/2s backoff)
- **Tool errors**: caught and fed back to LLM for self-correction

### Tools

| Tool | Description |
|------|-------------|
| `web_search` | Real web search via Baidu — returns titles, snippets, and source URLs |
| `save_note` | Save structured knowledge notes to long-term memory |
| `search_notes` | Search existing notes by keyword (returns full content) |
| `summarize` | Summarize text via LLM (with extractive fallback) |
| `calculator` | Safe math expression evaluation |
| `translate` | Translate text via LLM (with fallback) |
| `export_doc` | Export notes/results as files: md (default), docx, txt, html |

## Memory Mechanism

### Two-Layer Memory

```
+-------------------------+
| Short-term Memory       |
| * Full message history  |
| * Injected into every   |
|   LLM call              |
| * Persisted as JSON     |
| * Recoverable across    |
|   sessions              |
+-------------------------+
| Long-term Memory        |
| * Knowledge notes saved |
|   by user via save_note |
| * Persisted as JSON     |
| * Permanent retention   |
+-------------------------+
```

### Recall Timing & Placement

| | Short-term Memory | Long-term Memory |
|---|---|---|
| **Content** | All conversation messages (user/assistant/tool) | Knowledge notes saved via `save_note` |
| **Placement** | Auto-appended on each interaction | When Agent calls `save_note` tool |
| **Recall** | Full injection into every LLM call | Keyword-matched auto-injection into system prompt + Agent can call `search_notes` |
| **Storage** | `data/sessions/<id>.json` -> `messages` | `data/sessions/<id>.json` -> `notes` |
| **Cross-Session** | Recoverable (JSON persistence) | Permanent |

### Cross-Turn Continuity

```
Turn 1: "Research Transformer architecture"
  -> web_search -> save_note -> Finish
  -> Knowledge base: [note_1: "Transformer core principles..."]

(Close program, reopen)

Turn 2: "What's the formula for attention mechanism?"
  -> Runtime auto keyword-match: "attention mechanism" hits note_1
  -> System prompt injected: "Relevant Notes: [note_1] Transformer core principles..."
  -> LLM answers based on existing notes (or searches for more via search_notes)
```

## Project Structure

```
simpleAgent/
├── main.py                 # CLI entry point
├── demo.py                 # Demo script
├── requirements.txt        # Dependencies
├── README.md               # This file
├── agent/
│   ├── runtime.py          # AgentRuntime - core ReAct loop
│   ├── llm_client.py       # DeepSeek API wrapper
│   └── tool_registry.py    # Tool registration & dispatch
├── tools/
│   ├── base.py             # Tool ABC + data types (Note, Session)
│   ├── calculator.py       # Safe math calculator
│   ├── web_search.py       # Web search (real Baidu search)
│   ├── notes.py            # save_note + search_notes
│   ├── summarize.py        # LLM text summarizer
│   ├── translate.py        # LLM translator
│   └── export_doc.py       # Export to md/docx/txt/html
├── session/
│   └── manager.py          # Session persistence & note retrieval
├── templates/
│   ├── index.html          # Web chat UI
│   └── notes.html          # Notes viewer page
├── web.py                  # Flask web server
├── data/                   # Persistence directories
│   ├── sessions/
│   ├── notes/
│   └── exports/
└── tests/                  # Test suite (72 tests)
    ├── test_tool_base.py
    ├── test_calculator.py
    ├── test_web_search.py
    ├── test_notes.py
    ├── test_summarize.py
    ├── test_translate.py
    ├── test_tool_registry.py
    ├── test_llm_client.py
    ├── test_session_manager.py
    ├── test_runtime.py
    ├── test_integration.py
    └── test_export_doc.py
```

## Design Decisions

- **No Agent frameworks**: Core runtime (`agent/runtime.py`) implements the ReAct loop manually — no LangChain, AutoGen, or CrewAI.
- **Function Calling protocol**: Uses DeepSeek's OpenAI-compatible tool calling API rather than hand-parsing Thought/Action text.
- **Two-layer memory**: Short-term (conversation messages) + Long-term (knowledge notes) — both JSON-persisted.
- **Keyword-based retrieval**: Simple and predictable keyword matching for note injection; no embedding vector DB needed for this scope.
- **Max steps + error retry**: Prevents runaway loops and makes the agent resilient to API failures.

## License

MIT
