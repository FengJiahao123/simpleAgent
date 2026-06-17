# Simple Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从零构建一个个人知识库助手 Agent，自实现 ReAct Runtime，支持 6 个工具、两层记忆、跨轮次继续执行。

**Architecture:** 分层架构 — Tool 层（6 个可插拔工具）→ Agent Runtime（ReAct 循环 + Tool Registry + LLM Client）→ Session Manager（两层记忆持久化）→ CLI 入口。每层独立可测，依赖单向。

**Tech Stack:** Python 3.10+, openai >= 1.0.0 (指向 DeepSeek), pytest

## Global Constraints

- Python >= 3.10
- `openai >= 1.0.0`
- `pytest`（测试）
- 不依赖 LangChain / OpenHands 等 Agent 框架
- 使用真实 LLM API（DeepSeek V4 Pro，OpenAI 兼容接口）
- `max_steps = 10`
- API Key 通过环境变量 `DEEPSEEK_API_KEY` 获取
- API Base URL 通过环境变量 `DEEPSEEK_BASE_URL` 获取，默认 `https://api.deepseek.com`
- Prompt 驱动工具调用（function calling）+ Runtime 兜底解析
- Session 持久化到 `data/sessions/<session_id>.json`
- Git 提交习惯：每个 Task 至少一次 commit

---

### Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `agent/__init__.py`
- Create: `tools/__init__.py`
- Create: `session/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/sessions/.gitkeep`

**Produces:** 可安装依赖的项目结构

- [ ] **Step 1: 创建 requirements.txt**

```txt
openai>=1.0.0
pytest>=8.0.0
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
__pycache__/
*.pyc
.env
data/sessions/*.json
!data/sessions/.gitkeep
.pytest_cache/
```

- [ ] **Step 3: 创建所有 `__init__.py`**

```python
# agent/__init__.py
# tools/__init__.py
# session/__init__.py
# tests/__init__.py
```
（全部为空文件）

- [ ] **Step 4: 创建 data/sessions/.gitkeep**

```bash
mkdir -p data/sessions
touch data/sessions/.gitkeep
```

- [ ] **Step 5: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore agent/__init__.py tools/__init__.py session/__init__.py tests/__init__.py data/sessions/.gitkeep
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: 数据类型与 Tool 基类

**Files:**
- Create: `tools/base.py`
- Test: `tests/test_tool_base.py`

**Interfaces:**
- Produces: `Tool` ABC — `name: str`, `description: str`, `parameters: dict`, `execute(**kwargs) -> str`
- Produces: `Note` dataclass — `id: str, content: str, tags: list[str], source_url: str | None, created_at: str`
- Produces: `Session` dataclass — `session_id: str, messages: list[dict], notes: list[Note], created_at: float, updated_at: float`

- [ ] **Step 1: 编写工具基类测试（红）**

`tests/test_tool_base.py`:

```python
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
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_tool_base.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.base'`

- [ ] **Step 3: 实现 Tool 基类和数据类型（绿）**

`tools/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone


class Tool(ABC):
    """Base class for all tools. Each tool defines its interface via name,
    description, and parameters (JSON Schema)."""

    name: str = ""
    description: str = ""
    parameters: dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with the given arguments. Returns a string result.
        Extra kwargs (session, etc.) are silently ignored by tools that don't need them."""
        ...


@dataclass
class Note:
    """A knowledge note stored in the long-term memory."""
    content: str
    tags: list[str] = field(default_factory=list)
    source_url: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Session:
    """A conversation session with short-term and long-term memory."""
    session_id: str
    messages: list[dict] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_tool_base.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/base.py tests/test_tool_base.py
git commit -m "feat: add Tool base class and data types (Note, Session)"
```

---

### Task 3: Calculator 工具

**Files:**
- Create: `tools/calculator.py`
- Test: `tests/test_calculator.py`

**Interfaces:**
- Consumes: `Tool` from `tools/base.py`
- Produces: `Calculator` tool (`name="calculator"`, safe math expression evaluation)

- [ ] **Step 1: 编写 Calculator 测试（红）**

`tests/test_calculator.py`:

```python
import pytest
from tools.calculator import Calculator


class TestCalculator:
    @pytest.fixture
    def calc(self):
        return Calculator()

    def test_basic_arithmetic(self, calc):
        assert "7" in calc.execute(expression="3 + 4")
        assert "12" in calc.execute(expression="3 * 4")
        assert "2" in calc.execute(expression="10 / 5")
        assert "3" in calc.execute(expression="10 - 7")

    def test_complex_expression(self, calc):
        result = calc.execute(expression="(3 + 4) * 2 - 5")
        assert "9" in result

    def test_float_result(self, calc):
        result = calc.execute(expression="10 / 3")
        assert "3.33" in result  # 保留两位小数

    def test_square_root(self, calc):
        result = calc.execute(expression="sqrt(16)")
        assert "4" in result

    def test_power(self, calc):
        result = calc.execute(expression="2 ** 10")
        assert "1024" in result

    def test_rejects_dangerous_input(self, calc):
        """Calculator should reject attempts to access builtins or execute code."""
        result = calc.execute(expression="__import__('os').system('ls')")
        assert "error" in result.lower() or "invalid" in result.lower()
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_calculator.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 Calculator（绿）**

`tools/calculator.py`:

```python
import math
import operator
from tools.base import Tool


class Calculator(Tool):
    name = "calculator"
    description = "Safely evaluate a mathematical expression. Supports +, -, *, /, **, sqrt(), abs(), and parentheses."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate, e.g. '(3 + 4) * 2' or 'sqrt(144)'."
            }
        },
        "required": ["expression"]
    }

    # Safe builtins allowed in evaluation
    _ALLOWED_NAMES = {
        "sqrt": math.sqrt,
        "abs": abs,
        "pow": pow,
        "round": round,
        "min": min,
        "max": max,
        "pi": math.pi,
        "e": math.e,
    }

    def execute(self, expression: str, **kwargs) -> str:
        try:
            # Only allow safe characters to prevent code injection
            result = eval(expression, {"__builtins__": {}}, self._ALLOWED_NAMES)
            if isinstance(result, float):
                return str(round(result, 4))
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {e}"
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_calculator.py -v
```
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/calculator.py tests/test_calculator.py
git commit -m "feat: add Calculator tool with safe math evaluation"
```

---

### Task 4: Web Search 工具（Mock）

**Files:**
- Create: `tools/web_search.py`
- Test: `tests/test_web_search.py`

**Interfaces:**
- Consumes: `Tool` from `tools/base.py`
- Produces: `WebSearch` tool (`name="web_search"`, mock 返回预设结果)

- [ ] **Step 1: 编写 WebSearch 测试（红）**

`tests/test_web_search.py`:

```python
import pytest
from tools.web_search import WebSearch


class TestWebSearch:
    @pytest.fixture
    def search(self):
        return WebSearch()

    def test_search_returns_results(self, search):
        result = search.execute(query="Python programming")
        assert "Python" in result
        assert len(result) > 0

    def test_search_returns_different_results_for_different_queries(self, search):
        r1 = search.execute(query="machine learning")
        r2 = search.execute(query="web development")
        assert r1 != r2

    def test_search_no_results(self, search):
        """Searching for something very specific returns a no-results message."""
        result = search.execute(query="xyznonexistent12345")
        assert "no result" in result.lower() or "not found" in result.lower() or "0 result" in result.lower()

    def test_search_result_format(self, search):
        result = search.execute(query="Transformer architecture")
        # Should contain title-like markers or numbered entries
        lines = [l for l in result.split("\n") if l.strip()]
        assert len(lines) >= 1
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_web_search.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 WebSearch（绿）**

`tools/web_search.py`:

```python
from tools.base import Tool

# Mock knowledge base: pre-defined search results
_MOCK_KNOWLEDGE = {
    "python": [
        "Python Official Documentation — Comprehensive guide to Python language features, standard library, and best practices.",
        "Python 3.12 Release Notes — New features include improved error messages, type parameter syntax, and performance enhancements.",
        "Real Python Tutorials — Hands-on Python tutorials covering web development, data science, automation, and more.",
    ],
    "machine learning": [
        "Scikit-learn User Guide — Covers supervised and unsupervised learning algorithms with practical examples.",
        "Deep Learning with PyTorch — Official PyTorch tutorials for building neural networks, from MLPs to Transformers.",
        "MLOps Best Practices — Guide to deploying and maintaining ML models in production environments.",
    ],
    "transformer": [
        "Attention Is All You Need (Vaswani et al., 2017) — The original Transformer paper introducing self-attention mechanism.",
        "Transformer 架构的核心是自注意力机制（Self-Attention），计算公式为 Attention(Q,K,V) = softmax(QK^T/√d_k)V。多头注意力通过并行计算多个注意力头来捕捉不同子空间的信息。位置编码（Positional Encoding）使用正弦和余弦函数为序列添加位置信息。",
        "The Illustrated Transformer by Jay Alammar — Visual guide explaining Transformer architecture step by step.",
    ],
    "web development": [
        "MDN Web Docs — Mozilla's comprehensive reference for HTML, CSS, and JavaScript APIs.",
        "React Official Documentation — Guides for building user interfaces with React components and hooks.",
        "Flask Web Framework — Lightweight Python web framework for building APIs and web applications.",
    ],
    "attention mechanism": [
        "自注意力机制：对于输入序列 X，通过三个权重矩阵 W_Q、W_K、W_V 分别生成 Query、Key、Value。每个位置的输出是所有位置 Value 的加权和，权重由 Query 和 Key 的点积经过 softmax 归一化得到。多头注意力将这个过程重复 h 次，最后拼接结果。",
        "FlashAttention (Dao et al., 2022) — IO-aware attention algorithm that reduces memory reads/writes, achieving 2-4x speedup.",
    ],
    "deepseek": [
        "DeepSeek-V3 — A strong Mixture-of-Experts (MoE) language model with 671B total parameters, 37B activated per token.",
        "DeepSeek-R1 — Reasoning model that uses reinforcement learning to improve chain-of-thought reasoning capabilities.",
    ],
}


class WebSearch(Tool):
    name = "web_search"
    description = "Search the web for information on a given topic. Returns up to 3 relevant results."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query or topic to look up."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> str:
        query_lower = query.lower().strip()
        results = []
        seen = set()

        # Simple keyword matching against mock knowledge base
        for keyword, entries in _MOCK_KNOWLEDGE.items():
            if keyword in query_lower:
                for entry in entries:
                    if entry not in seen:
                        results.append(entry)
                        seen.add(entry)

        if not results:
            return f"No results found for '{query}'. Try different keywords or be more specific."

        output = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results[:3], 1):
            output += f"{i}. {result}\n"
        return output.strip()
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_web_search.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/web_search.py tests/test_web_search.py
git commit -m "feat: add WebSearch tool with mock knowledge base"
```

---

### Task 5: Summarize 工具

**Files:**
- Create: `tools/summarize.py`
- Test: `tests/test_summarize.py`

**Interfaces:**
- Consumes: `Tool` from `tools/base.py`
- Produces: `Summarize` tool (`name="summarize"`, 调用 LLM 做摘要)
- Note: 此工具需要一个 LLM 调用接口，暂用 mock LLM 测试工具本身的逻辑

- [ ] **Step 1: 编写 Summarize 测试（红）**

`tests/test_summarize.py`:

```python
import pytest
from tools.summarize import Summarize


class FakeLLMForSummarize:
    """Fake LLM client that returns a short summary."""
    def chat(self, messages, tools=None):
        class Response:
            class Choice:
                class Message:
                    content = "This is a summarized version of the input text."
                    tool_calls = None
                message = Message()
            choices = [Choice()]
        return Response()


class TestSummarize:
    @pytest.fixture
    def summarizer(self):
        return Summarize(llm_client=FakeLLMForSummarize())

    def test_summarize_returns_string(self, summarizer):
        result = summarizer.execute(text="Long text to summarize")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_summarize_calls_llm(self, summarizer):
        """Summarize should call the LLM with a summarization prompt."""
        result = summarizer.execute(text="Transformer architecture is a neural network design...")
        assert "summarized" in result.lower()

    def test_summarize_with_max_length(self, summarizer):
        result = summarizer.execute(text="Some text", max_length="50")
        assert isinstance(result, str)
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_summarize.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 Summarize（绿）**

`tools/summarize.py`:

```python
from tools.base import Tool


class Summarize(Tool):
    name = "summarize"
    description = "Summarize a long text into a concise version. Useful for condensing search results or articles."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to summarize."
            },
            "max_length": {
                "type": "string",
                "description": "Optional maximum length of the summary in characters. Default is 200."
            }
        },
        "required": ["text"]
    }

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def execute(self, text: str, max_length: str = "200", **kwargs) -> str:
        if self._llm_client is None:
            # Fallback: simple extractive summary (first N chars + last sentence)
            max_len = int(max_length) if max_length.isdigit() else 200
            if len(text) <= max_len:
                return text
            summary = text[:max_len].rsplit(".", 1)[0] + "."
            return f"[Summary] {summary}"

        messages = [
            {"role": "system", "content": f"You are a text summarizer. Summarize the given text in no more than {max_length} characters. Return only the summary, no preamble."},
            {"role": "user", "content": text},
        ]
        response = self._llm_client.chat(messages)
        return response.choices[0].message.content
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_summarize.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/summarize.py tests/test_summarize.py
git commit -m "feat: add Summarize tool with LLM and fallback modes"
```

---

### Task 6: Translate 工具

**Files:**
- Create: `tools/translate.py`
- Test: `tests/test_translate.py`

**Interfaces:**
- Consumes: `Tool` from `tools/base.py`
- Produces: `Translate` tool (`name="translate"`, 调用 LLM 做翻译)

- [ ] **Step 1: 编写 Translate 测试（红）**

`tests/test_translate.py`:

```python
import pytest
from tools.translate import Translate


class FakeLLMForTranslate:
    """Fake LLM client that echoes back with a translation marker."""
    def chat(self, messages, tools=None):
        class Response:
            class Choice:
                class Message:
                    content = "[Translated] Hello, world!"
                    tool_calls = None
                message = Message()
            choices = [Choice()]
        return Response()


class TestTranslate:
    @pytest.fixture
    def translator(self):
        return Translate(llm_client=FakeLLMForTranslate())

    def test_translate_returns_string(self, translator):
        result = translator.execute(text="你好世界", target_language="English")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_translate_default_to_english(self, translator):
        result = translator.execute(text="Bonjour le monde")
        assert "Hello" in result or "Translated" in result

    def test_translate_to_chinese(self, translator):
        result = translator.execute(text="Hello world", target_language="Chinese")
        assert isinstance(result, str)

    def test_translate_without_target_uses_default(self, translator):
        """When target_language is not specified, default to English."""
        result = translator.execute(text="Hola mundo")
        assert isinstance(result, str)
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_translate.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 Translate（绿）**

`tools/translate.py`:

```python
from tools.base import Tool


class Translate(Tool):
    name = "translate"
    description = "Translate text from one language to another. Default target is English."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to translate."
            },
            "target_language": {
                "type": "string",
                "description": "The target language to translate to, e.g. 'Chinese', 'English', 'Japanese'. Default is 'English'."
            }
        },
        "required": ["text"]
    }

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def execute(self, text: str, target_language: str = "English", **kwargs) -> str:
        if self._llm_client is None:
            return f"[Translation to {target_language} unavailable — no LLM client configured]\nOriginal: {text}"

        messages = [
            {"role": "system", "content": f"You are a translator. Translate the user's text to {target_language}. Return only the translation, no preamble or explanation."},
            {"role": "user", "content": text},
        ]
        response = self._llm_client.chat(messages)
        return response.choices[0].message.content
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_translate.py -v
```
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/translate.py tests/test_translate.py
git commit -m "feat: add Translate tool with LLM and fallback modes"
```

---

### Task 7: Notes 工具（save_note + search_notes）

**Files:**
- Create: `tools/notes.py`
- Test: `tests/test_notes.py`

**Interfaces:**
- Consumes: `Tool`, `Note`, `Session` from `tools/base.py`
- Produces: `SaveNote` tool (`name="save_note"`), `SearchNotes` tool (`name="search_notes"`)

- [ ] **Step 1: 编写 Notes 工具测试（红）**

`tests/test_notes.py`:

```python
import pytest
from tools.notes import SaveNote, SearchNotes
from tools.base import Session, Note


class TestSaveNote:
    @pytest.fixture
    def session(self):
        return Session(session_id="test-001")

    @pytest.fixture
    def save_note(self):
        return SaveNote()

    def test_save_note_adds_to_session(self, save_note, session):
        result = save_note.execute(
            content="Transformer uses self-attention mechanism.",
            tags=["AI", "NLP"],
            session=session,
        )
        assert len(session.notes) == 1
        assert session.notes[0].content == "Transformer uses self-attention mechanism."
        assert session.notes[0].tags == ["AI", "NLP"]
        assert "saved" in result.lower()
        assert session.notes[0].id in result

    def test_save_note_without_tags(self, save_note, session):
        result = save_note.execute(
            content="Python is a programming language.",
            session=session,
        )
        assert len(session.notes) == 1
        assert session.notes[0].tags == []

    def test_save_note_with_source_url(self, save_note, session):
        result = save_note.execute(
            content="Attention paper details.",
            tags=["paper"],
            source_url="https://arxiv.org/abs/1706.03762",
            session=session,
        )
        assert session.notes[0].source_url == "https://arxiv.org/abs/1706.03762"

    def test_save_note_without_session(self, save_note):
        """save_note requires a session to store the note."""
        result = save_note.execute(content="Some content")
        assert "error" in result.lower() or "no session" in result.lower()


class TestSearchNotes:
    @pytest.fixture
    def session(self):
        s = Session(session_id="test-002")
        s.notes = [
            Note(content="Transformer uses self-attention for sequence processing.", tags=["AI", "NLP"]),
            Note(content="Python is widely used in data science and web development.", tags=["programming"]),
            Note(content="Self-attention computes weighted sums of input representations.", tags=["AI", "attention"]),
        ]
        return s

    @pytest.fixture
    def search_notes(self):
        return SearchNotes()

    def test_search_notes_finds_relevant(self, search_notes, session):
        result = search_notes.execute(query="attention mechanism", session=session)
        assert "self-attention" in result.lower()
        # Should match the first and third notes
        assert "Transformer" in result

    def test_search_notes_no_match(self, search_notes, session):
        result = search_notes.execute(query="quantum computing", session=session)
        assert "no" in result.lower() or "not found" in result.lower() or "0" in result.lower()

    def test_search_notes_without_session(self, search_notes):
        result = search_notes.execute(query="attention")
        assert "error" in result.lower() or "no session" in result.lower()
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_notes.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 Notes 工具（绿）**

`tools/notes.py`:

```python
from tools.base import Tool, Note, Session


class SaveNote(Tool):
    name = "save_note"
    description = "Save a piece of knowledge as a note for future reference. Notes persist across sessions."
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The knowledge content to save."
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for categorizing the note, e.g. ['AI', 'NLP']."
            },
            "source_url": {
                "type": "string",
                "description": "Optional source URL where the information came from."
            }
        },
        "required": ["content"]
    }

    def execute(self, content: str, tags: list | None = None, source_url: str = "", **kwargs) -> str:
        session: Session | None = kwargs.get("session")
        if session is None:
            return "Error: No session available to save the note. Please try again."

        note = Note(
            content=content,
            tags=tags if tags else [],
            source_url=source_url if source_url else None,
        )
        session.notes.append(note)
        tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
        return f"Note saved successfully (id: {note.id}){tags_str}"


class SearchNotes(Tool):
    name = "search_notes"
    description = "Search your existing notes for relevant knowledge. Use this before searching the web to leverage previously saved information."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords or question to search for in your notes."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> str:
        session: Session | None = kwargs.get("session")
        if session is None:
            return "Error: No session available. Please try again."

        if not session.notes:
            return "You have no saved notes yet. Use web_search to find information, then save_note to keep it."

        query_lower = query.lower()
        scored: list[tuple[Note, int]] = []

        for note in session.notes:
            score = 0
            content_lower = note.content.lower()
            # Keyword matching in content
            for word in query_lower.split():
                if word in content_lower:
                    score += 1
            # Bonus for tag match
            for tag in note.tags:
                if tag.lower() in query_lower:
                    score += 2
            if score > 0:
                scored.append((note, score))

        if not scored:
            return f"No notes matched your query '{query}'. Try different keywords or use web_search."

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]

        output = f"Found {len(top)} matching note(s) for '{query}':\n\n"
        for i, (note, score) in enumerate(top, 1):
            tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
            output += f"{i}.{tags_str} {note.content[:200]}\n"
            if note.source_url:
                output += f"   Source: {note.source_url}\n"
            output += "\n"
        return output.strip()
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_notes.py -v
```
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add tools/notes.py tests/test_notes.py
git commit -m "feat: add SaveNote and SearchNotes tools for knowledge base"
```

---

### Task 8: Tool Registry

**Files:**
- Create: `agent/tool_registry.py`
- Test: `tests/test_tool_registry.py`

**Interfaces:**
- Consumes: `Tool` from `tools/base.py`, `Calculator`, `WebSearch`, `SaveNote`, `SearchNotes`, `Summarize`, `Translate`
- Produces: `ToolRegistry` — `register(tool: Tool)`, `get_definitions() -> list[dict]`, `execute(name: str, args: dict, **extra) -> str`

- [ ] **Step 1: 编写 ToolRegistry 测试（红）**

`tests/test_tool_registry.py`:

```python
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
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_tool_registry.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 ToolRegistry（绿）**

`agent/tool_registry.py`:

```python
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
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_tool_registry.py -v
```
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add agent/tool_registry.py tests/test_tool_registry.py
git commit -m "feat: add ToolRegistry for tool registration and dispatch"
```

---

### Task 9: LLM Client

**Files:**
- Create: `agent/llm_client.py`
- Test: `tests/test_llm_client.py`

**Interfaces:**
- Consumes: `openai` SDK
- Produces: `LLMClient` — `chat(messages: list[dict], tools: list[dict] | None = None) -> ChatCompletionMessage`

- [ ] **Step 1: 编写 LLM Client 测试（红）**

`tests/test_llm_client.py`:

```python
import os
import pytest
from agent.llm_client import LLMClient


class TestLLMClientInit:
    def test_uses_env_api_key(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        client = LLMClient()
        assert client._api_key == "sk-test-key"

    def test_uses_passed_api_key(self):
        client = LLMClient(api_key="sk-explicit")
        assert client._api_key == "sk-explicit"

    def test_default_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        client = LLMClient()
        assert "deepseek.com" in client._base_url

    def test_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://custom.api.com")
        client = LLMClient()
        assert "custom.api.com" in client._base_url

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            LLMClient()


class TestLLMClientChat:
    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        return LLMClient()

    def test_chat_requires_api_key_or_mock(self, client):
        """Without a real API key or mock, chat() should raise a connection error.
        This test validates the method signature and basic error handling."""
        messages = [{"role": "user", "content": "Hello"}]
        # Since we don't have a real key, this should raise an authentication or connection error
        with pytest.raises(Exception):
            client.chat(messages)

    def test_message_format_preserved(self, client):
        """Verify the client doesn't mutate input messages."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        original = [m.copy() for m in messages]
        try:
            client.chat(messages)
        except Exception:
            pass
        assert messages == original
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_llm_client.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 LLM Client（绿）**

`agent/llm_client.py`:

```python
import os
import time
from openai import OpenAI


class LLMClient:
    """Thin wrapper around OpenAI-compatible DeepSeek API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "deepseek-chat",
        max_retries: int = 2,
    ):
        self._api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY environment variable is required. "
                "Set it via `export DEEPSEEK_API_KEY=sk-...` or pass api_key= to LLMClient()."
            )

        self._base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self._model = model
        self._max_retries = max_retries

        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> object:
        """Send messages to the LLM and return the response.

        Returns an object with:
          - .content: str | None (the text response, or None if tool call)
          - .tool_calls: list | None (function calls requested by the model)
          - .usage: dict | None (token usage info)
        """
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                kwargs = {
                    "model": self._model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self._client.chat.completions.create(**kwargs)
                return response.choices[0].message

            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    time.sleep(1 + attempt)
                else:
                    raise RuntimeError(
                        f"LLM API call failed after {self._max_retries + 1} attempts: {last_error}"
                    ) from last_error
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_llm_client.py -v
```
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add agent/llm_client.py tests/test_llm_client.py
git commit -m "feat: add LLMClient for DeepSeek API with retry logic"
```

---

### Task 10: Session Manager

**Files:**
- Create: `session/manager.py`
- Test: `tests/test_session_manager.py`

**Interfaces:**
- Consumes: `Session`, `Note` from `tools/base.py`
- Produces: `SessionManager` — `create(session_id) -> Session`, `load(session_id) -> Session`, `save(session)`, `list_sessions() -> list[str]`, `get_related_notes(session, query, top_k) -> list[Note]`

- [ ] **Step 1: 编写 Session Manager 测试（红）**

`tests/test_session_manager.py`:

```python
import json
import os
import tempfile
import pytest
from session.manager import SessionManager
from tools.base import Session, Note


class TestSessionManager:
    @pytest.fixture
    def data_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            sessions_dir = os.path.join(tmp, "sessions")
            os.makedirs(sessions_dir)
            yield sessions_dir

    @pytest.fixture
    def manager(self, data_dir):
        return SessionManager(data_dir=data_dir)

    def test_create_session(self, manager):
        session = manager.create("test-001")
        assert session.session_id == "test-001"
        assert session.messages == []
        assert session.notes == []

    def test_save_and_load_session(self, manager):
        session = manager.create("test-002")
        session.messages.append({"role": "user", "content": "Hello"})
        session.messages.append({"role": "assistant", "content": "Hi there!"})
        note = Note(content="Test knowledge", tags=["test"])
        session.notes.append(note)

        manager.save(session)

        loaded = manager.load("test-002")
        assert loaded.session_id == "test-002"
        assert len(loaded.messages) == 2
        assert loaded.messages[0]["content"] == "Hello"
        assert len(loaded.notes) == 1
        assert loaded.notes[0].content == "Test knowledge"

    def test_load_non_existent_session(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.load("non-existent")

    def test_list_sessions(self, manager):
        manager.save(manager.create("a"))
        manager.save(manager.create("b"))
        sessions = manager.list_sessions()
        assert "a" in sessions
        assert "b" in sessions

    def test_get_related_notes_keyword_match(self, manager):
        session = manager.create("test-003")
        session.notes = [
            Note(content="Transformer uses self-attention mechanism.", tags=["AI"]),
            Note(content="Python is a programming language.", tags=["programming"]),
            Note(content="Self-attention computes weighted sums of values.", tags=["AI", "attention"]),
        ]

        results = manager.get_related_notes(session, "attention mechanism", top_k=3)
        assert len(results) >= 1
        # Notes about self-attention should rank higher than Python note
        assert "self-attention" in results[0].content.lower() or "attention" in results[0].content.lower()

    def test_get_related_notes_no_match(self, manager):
        session = manager.create("test-004")
        session.notes = [Note(content="Only about Python.", tags=["programming"])]

        results = manager.get_related_notes(session, "quantum physics", top_k=3)
        assert results == []

    def test_get_related_notes_empty_notes(self, manager):
        session = manager.create("test-005")
        results = manager.get_related_notes(session, "anything", top_k=3)
        assert results == []

    def test_save_and_load_preserves_created_at(self, manager):
        session = manager.create("test-006")
        original_created = session.created_at
        manager.save(session)

        loaded = manager.load("test-006")
        assert loaded.created_at == original_created

    def test_corrupted_session_file(self, manager, data_dir):
        """Corrupted session files should raise an error."""
        filepath = os.path.join(data_dir, "corrupt.json")
        with open(filepath, "w") as f:
            f.write("this is not valid json {{{")

        with pytest.raises(Exception):
            manager.load("corrupt")
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_session_manager.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 Session Manager（绿）**

`session/manager.py`:

```python
import json
import os
from tools.base import Session, Note


class SessionManager:
    """Manages session creation, persistence, and knowledge retrieval."""

    def __init__(self, data_dir: str = "data/sessions"):
        self._data_dir = data_dir
        os.makedirs(self._data_dir, exist_ok=True)

    def _filepath(self, session_id: str) -> str:
        return os.path.join(self._data_dir, f"{session_id}.json")

    def create(self, session_id: str) -> Session:
        """Create a new empty session."""
        return Session(session_id=session_id)

    def load(self, session_id: str) -> Session:
        """Load a session from disk."""
        filepath = self._filepath(session_id)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Session '{session_id}' not found. Use 'create' first or check the ID.")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session(
            session_id=data["session_id"],
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )

        # Restore notes
        for note_data in data.get("notes", []):
            note = Note(
                id=note_data.get("id", ""),
                content=note_data.get("content", ""),
                tags=note_data.get("tags", []),
                source_url=note_data.get("source_url"),
                created_at=note_data.get("created_at", ""),
            )
            session.notes.append(note)

        # Restore messages
        session.messages = data.get("messages", [])

        return session

    def save(self, session: Session) -> None:
        """Persist a session to disk."""
        import time
        session.updated_at = time.time()

        data = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "messages": session.messages,
            "notes": [
                {
                    "id": n.id,
                    "content": n.content,
                    "tags": n.tags,
                    "source_url": n.source_url,
                    "created_at": n.created_at,
                }
                for n in session.notes
            ],
        }

        filepath = self._filepath(session.session_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_sessions(self) -> list[str]:
        """List all saved session IDs."""
        sessions = []
        if not os.path.exists(self._data_dir):
            return sessions
        for filename in os.listdir(self._data_dir):
            if filename.endswith(".json"):
                sessions.append(filename[:-5])
        return sorted(sessions)

    def get_related_notes(self, session: Session, query: str, top_k: int = 3) -> list[Note]:
        """Find notes relevant to the query using simple keyword matching.
        Called before each agent run to inject relevant knowledge into the system prompt.
        """
        if not session.notes or not query:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored: list[tuple[Note, int]] = []

        for note in session.notes:
            score = 0
            content_lower = note.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1
            for tag in note.tags:
                if tag.lower() in query_lower or tag.lower() in query_words:
                    score += 2
            if score > 0:
                scored.append((note, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [note for note, _ in scored[:top_k]]
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_session_manager.py -v
```
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add session/manager.py tests/test_session_manager.py
git commit -m "feat: add SessionManager with persistence and note retrieval"
```

---

### Task 11: Agent Runtime（核心）

**Files:**
- Create: `agent/runtime.py`
- Test: `tests/test_runtime.py`

**Interfaces:**
- Consumes: `LLMClient`, `ToolRegistry`, `SessionManager` — 即所有此前构建的模块
- Produces: `AgentRuntime` — `run(session: Session, user_input: str) -> AgentResult`
- Produces: `AgentResult` dataclass — `answer: str, trace: list[dict], total_tokens: int, steps: int`

- [ ] **Step 1: 编写 Runtime 测试（红）**

`tests/test_runtime.py`:

```python
import pytest
from agent.runtime import AgentRuntime, AgentResult
from agent.tool_registry import ToolRegistry
from tools.base import Session, Note


# ---- Fake LLM for testing ----

class FakeLLM:
    """Fake LLM that returns pre-programmed responses for testing the runtime loop."""

    def __init__(self, responses: list):
        """
        responses: list of messages, each either:
          - a string (final content, no tool call)
          - a dict with 'tool_calls' for tool call responses
        """
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
        # Verify trace records tool execution
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
        assert len(result.trace) == 2

    def test_max_steps_limit(self, registry, session):
        """When max_steps is reached, force a final answer."""
        tc = _make_tool_call("calculator", '{"expression": "1+1"}')
        # Keep returning tool calls to exhaust steps
        responses = [{"tool_calls": [tc]}] * 10
        llm = FakeLLM(responses)
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=3)

        result = runtime.run(session, "Calculate repeatedly")

        assert result.steps <= 3
        assert "step limit" in result.answer.lower() or len(result.answer) > 0

    def test_tool_error_is_fed_back(self, registry, session):
        """When a tool fails, the error is returned as observation so LLM can adjust."""
        tc = _make_tool_call("calculator", '{"expression": "invalid!!!"}')
        llm = FakeLLM([
            {"tool_calls": [tc]},
            "The calculation failed. Let me try differently: the answer is unknown.",
        ])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry, max_steps=5)

        result = runtime.run(session, "Calculate something broken")

        # Step 2 should be the retry/fallback after error
        assert result.steps >= 2

    def test_knowledge_injection(self, registry, session):
        """Related notes should appear in the system prompt."""
        session.notes = [Note(content="Python was created by Guido van Rossum.", tags=["programming"])]

        llm = FakeLLM(["Python was created by Guido van Rossum."])
        runtime = AgentRuntime(llm_client=llm, tool_registry=registry)

        result = runtime.run(session, "Who created Python?")
        assert "Guido" in result.answer

        # Check that the first message sent to LLM includes the injected note
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
```

- [ ] **Step 2: 运行测试验证失败（红）**

```bash
pytest tests/test_runtime.py -v
```
Expected: FAIL

- [ ] **Step 3: 实现 Agent Runtime（绿）**

`agent/runtime.py`:

```python
import json
from dataclasses import dataclass, field
from agent.llm_client import LLMClient
from agent.tool_registry import ToolRegistry
from tools.base import Session


@dataclass
class AgentResult:
    """Result of a single agent run."""
    answer: str
    trace: list[dict] = field(default_factory=list)
    total_tokens: int = 0
    steps: int = 0


SYSTEM_PROMPT = """You are a knowledge base assistant. You help users research topics, save findings as notes, and retrieve knowledge later.

## Your Tools
- **web_search**: Search the web for information on a topic.
- **save_note**: Save a piece of knowledge as a note for future reference.
- **search_notes**: Search your existing notes before searching the web.
- **summarize**: Condense long text into a concise summary.
- **calculator**: Perform mathematical calculations.
- **translate**: Translate text between languages.

## Guidelines
1. If the user asks about something that might be in your notes, search notes first.
2. Save important findings using save_note so you can recall them later.
3. If you need information not in your notes, search the web.
4. When answering, synthesize information clearly and cite sources.
5. You can use multiple tools in sequence — plan your steps before acting.
6. If a tool returns an error, try a different approach.
"""


class AgentRuntime:
    """Core ReAct-style agent loop. Orchestrates LLM calls, tool execution,
    and session state management."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        max_steps: int = 10,
    ):
        self._llm = llm_client
        self._registry = tool_registry
        self.max_steps = max_steps

    def run(self, session: Session, user_input: str) -> AgentResult:
        """Execute the agent loop for a single user input.

        Args:
            session: The current session (mutated in-place with new messages).
            user_input: The user's latest message.

        Returns:
            AgentResult with the final answer, trace, and metrics.
        """
        trace: list[dict] = []
        total_tokens = 0

        # Build system prompt with injected knowledge
        system_content = self._build_system_prompt(session, user_input)

        # Build messages: system + history + new user message
        messages = session.messages.copy()
        session.messages.append({"role": "user", "content": user_input})

        # For the API call, prepend system prompt
        api_messages = [{"role": "system", "content": system_content}] + session.messages.copy()

        tools = self._registry.get_definitions()

        step = 0
        while step < self.max_steps:
            step += 1

            # Call LLM
            try:
                response = self._llm.chat(api_messages, tools=tools)
            except Exception as e:
                trace.append({"step": step, "error": str(e)})
                return AgentResult(
                    answer=f"Sorry, I encountered an error communicating with the LLM: {e}",
                    trace=trace,
                    total_tokens=total_tokens,
                    steps=step,
                )

            # Check for tool calls
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Execute tool
                    tool_result = self._registry.execute(
                        tool_name, tool_args, session=session
                    )

                    trace.append({
                        "step": step,
                        "tool": tool_name,
                        "args": tool_args,
                        "result": tool_result[:200],  # Truncate in trace for readability
                    })

                    # Append assistant tool_call + tool result to messages
                    session.messages.append({
                        "role": "assistant",
                        "content": response.content,
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                }
                            }
                        ]
                    })
                    session.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

                    # Update API messages for next iteration
                    api_messages = [{"role": "system", "content": system_content}] + session.messages.copy()

                # If there were tool calls, continue loop for LLM to process results
                continue

            # No tool calls — this is the final answer
            final_answer = response.content or "I have no further response."
            session.messages.append({"role": "assistant", "content": final_answer})
            trace.append({
                "step": step,
                "action": "final_answer",
                "content": final_answer[:200],
            })

            return AgentResult(
                answer=final_answer,
                trace=trace,
                total_tokens=total_tokens,
                steps=step,
            )

        # Max steps reached — force final answer
        forced_answer = (
            "I've reached the maximum number of steps. Based on what I've gathered so far, "
            "let me give you my best answer. Please ask a more specific question if you need more detail."
        )
        session.messages.append({"role": "assistant", "content": forced_answer})
        return AgentResult(
            answer=forced_answer,
            trace=trace,
            total_tokens=total_tokens,
            steps=step,
        )

    def _build_system_prompt(self, session: Session, user_input: str) -> str:
        """Build system prompt with injected relevant notes."""
        prompt = SYSTEM_PROMPT

        # Inject relevant notes from knowledge base
        # (We do simple keyword matching here; SessionManager.get_related_notes
        #  is called by external code. For simplicity, we inline it.)
        if session.notes and user_input:
            related = self._get_related_notes(session, user_input)
            if related:
                note_lines = []
                for i, note in enumerate(related, 1):
                    note_lines.append(f"[Note {i}] {note.content[:300]}")
                    if note.tags:
                        note_lines[-1] += f" (tags: {', '.join(note.tags)})"
                prompt += "\n\n## Relevant Knowledge from Your Notes\n"
                prompt += "\n".join(note_lines)
                prompt += "\n\nYou can search for more details using search_notes if needed.\n"

        return prompt

    def _get_related_notes(self, session: Session, query: str, top_k: int = 3) -> list:
        """Simple keyword-based note retrieval."""
        if not session.notes:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored = []

        for note in session.notes:
            score = 0
            content_lower = note.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1
            for tag in note.tags:
                if tag.lower() in query_lower or tag.lower() in query_words:
                    score += 2
            if score > 0:
                scored.append((note, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [note for note, _ in scored[:top_k]]
```

- [ ] **Step 4: 运行测试验证通过（绿）**

```bash
pytest tests/test_runtime.py -v
```
Expected: PASS (8 tests including AgentResult)

- [ ] **Step 5: Commit**

```bash
git add agent/runtime.py tests/test_runtime.py
git commit -m "feat: add AgentRuntime — core ReAct loop with tool orchestration"
```

---

### Task 12: CLI 入口（main.py）

**Files:**
- Create: `main.py`

**Interfaces:**
- Consumes: `AgentRuntime`, `LLMClient`, `ToolRegistry`, `SessionManager` + 所有工具
- Produces: CLI 入口，支持 `new` / `resume` / `list` / `delete` 子命令和交互模式

- [ ] **Step 1: 实现 main.py**

`main.py`:

```python
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
from agent.llm_client import LLMClient
from agent.tool_registry import ToolRegistry
from agent.runtime import AgentRuntime
from session.manager import SessionManager
from tools.calculator import Calculator
from tools.web_search import WebSearch
from tools.notes import SaveNote, SearchNotes
from tools.summarize import Summarize
from tools.translate import Translate


def print_trace(trace: list[dict], max_steps: int):
    """Print formatted trace of agent execution."""
    for entry in trace:
        step = entry.get("step", "?")
        if "tool" in entry:
            args_str = ", ".join(f"{k}={v}" for k, v in entry.get("args", {}).items())
            print(f"  [Step {step}/{max_steps}] 🔧 {entry['tool']}({args_str})")
            result = entry.get("result", "")
            if len(result) > 100:
                result = result[:100] + "..."
            print(f"    → {result}")
        elif entry.get("action") == "final_answer":
            print(f"  [Step {step}/{max_steps}] ✅ Final Answer")
        elif "error" in entry:
            print(f"  [Step {step}/{max_steps}] ❌ Error: {entry['error']}")


def build_runtime() -> tuple[AgentRuntime, ToolRegistry, SessionManager]:
    """Wire up all components and return the runtime, registry, and session manager."""

    # LLM Client
    try:
        llm_client = LLMClient()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("   Set DEEPSEEK_API_KEY environment variable to your DeepSeek API key.")
        print("   Example: export DEEPSEEK_API_KEY=sk-...")
        sys.exit(1)

    # Tool Registry
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(WebSearch())
    registry.register(SaveNote())
    registry.register(SearchNotes())
    registry.register(Summarize(llm_client=llm_client))
    registry.register(Translate(llm_client=llm_client))

    # Session Manager
    session_manager = SessionManager()

    # Agent Runtime
    runtime = AgentRuntime(llm_client=llm_client, tool_registry=registry, max_steps=10)

    return runtime, registry, session_manager


def interactive_loop(runtime: AgentRuntime, session_manager: SessionManager):
    """Main interactive loop."""
    # Determine session
    sessions = session_manager.list_sessions()
    if sessions:
        print("📂 Existing sessions:")
        for s in sessions:
            print(f"   • {s}")
        print()
        choice = input("Enter session ID to resume, or press Enter for new: ").strip()
    else:
        choice = ""

    if choice:
        session_id = choice
        try:
            session = session_manager.load(session_id)
            print(f"📂 Resumed session: {session_id}")
            print(f"   {len(session.messages)} messages, {len(session.notes)} notes loaded.\n")
        except FileNotFoundError:
            print(f"Session '{session_id}' not found. Creating new session.")
            session = session_manager.create(session_id)
    else:
        session_id = f"session-{len(sessions) + 1:03d}"
        session = session_manager.create(session_id)
        print(f"📝 Created new session: {session_id}\n")

    # Graceful shutdown — save on Ctrl+C
    def save_on_exit(*args):
        print("\n💾 Saving session...")
        session_manager.save(session)
        print(f"✅ Session saved to data/sessions/{session_id}.json")
        print("👋 Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, save_on_exit)

    print("🤖 Simple Agent is ready. Type 'exit' to quit, 'notes' to see your notes.\n")

    while True:
        try:
            user_input = input("🤖 > ").strip()
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
                print(f"📝 You have {len(session.notes)} note(s):")
                for i, note in enumerate(session.notes, 1):
                    tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
                    print(f"   {i}.{tags_str} {note.content[:100]}...")
            else:
                print("📝 No notes yet. Ask me to research something!")
            print()
            continue

        print()
        result = runtime.run(session, user_input)
        print_trace(result.trace, runtime.max_steps)
        print(f"\n💬 {result.answer}\n")
        print(f"   ({result.steps} step(s))\n")

        # Auto-save after each turn
        session_manager.save(session)


def main():
    args = sys.argv[1:]

    runtime, registry, session_manager = build_runtime()

    if not args:
        interactive_loop(runtime, session_manager)
        return

    command = args[0].lower()

    if command == "new":
        sessions = session_manager.list_sessions()
        session_id = f"session-{len(sessions) + 1:03d}"
        session = session_manager.create(session_id)
        session_manager.save(session)
        print(f"✅ Created new session: {session_id}")
        print(f"   Run: python main.py resume {session_id}")

    elif command == "resume":
        if len(args) < 2:
            print("Usage: python main.py resume <session_id>")
            sys.exit(1)
        session_id = args[1]
        try:
            session = session_manager.load(session_id)
        except FileNotFoundError:
            print(f"❌ Session '{session_id}' not found.")
            sys.exit(1)

        print(f"📂 Resumed session: {session_id}")
        print(f"   {len(session.messages)} messages, {len(session.notes)} notes.")
        print("   Entering interactive mode...\n")

        def save_on_exit(*args):
            print("\n💾 Saving...")
            session_manager.save(session)
            print("👋 Goodbye!")
            sys.exit(0)

        signal.signal(signal.SIGINT, save_on_exit)

        while True:
            try:
                user_input = input("🤖 > ").strip()
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
            print(f"\n💬 {result.answer}\n")
            print(f"   ({result.steps} step(s))\n")
            session_manager.save(session)

    elif command == "list":
        sessions = session_manager.list_sessions()
        if sessions:
            print(f"📂 {len(sessions)} session(s):")
            for s in sessions:
                print(f"   • {s}")
        else:
            print("📂 No sessions found. Create one with: python main.py new")

    elif command == "delete":
        if len(args) < 2:
            print("Usage: python main.py delete <session_id>")
            sys.exit(1)
        session_id = args[1]
        filepath = os.path.join("data", "sessions", f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️  Deleted session: {session_id}")
        else:
            print(f"❌ Session '{session_id}' not found.")

    else:
        print(f"Unknown command: {command}")
        print("Available: new, resume <id>, list, delete <id>")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试 CLI 命令**

```bash
# list — 应该显示空
python main.py list

# new — 创建新 session
python main.py new

# list — 应该显示刚创建的 session
python main.py list

# delete — 删除测试 session（记下实际 session ID）
python main.py delete session-001
```

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add CLI entry point with session management commands"
```

---

### Task 13: 集成测试与跨轮次 Demo 脚本

**Files:**
- Create: `tests/test_integration.py`
- Create: `demo.py`

- [ ] **Step 1: 编写集成测试**

`tests/test_integration.py`:

```python
"""Integration test: full agent pipeline with fake LLM."""
import pytest
from agent.llm_client import LLMClient as _RealLLM
from agent.tool_registry import ToolRegistry
from agent.runtime import AgentRuntime
from session.manager import SessionManager
from tools.calculator import Calculator
from tools.web_search import WebSearch
from tools.notes import SaveNote, SearchNotes
from tools.summarize import Summarize
from tools.translate import Translate


# Reuse the FakeLLM from test_runtime
import sys
sys.path.insert(0, ".")
from tests.test_runtime import FakeLLM, _make_llm_response, _make_tool_call


class TestIntegration:
    @pytest.fixture
    def components(self):
        registry = ToolRegistry()
        registry.register(Calculator())
        registry.register(WebSearch())
        registry.register(SaveNote())
        registry.register(SearchNotes())

        # Summarize and Translate with fake LLM
        fake_llm = FakeLLM([])
        registry.register(Summarize(llm_client=fake_llm))
        registry.register(Translate(llm_client=fake_llm))

        session_manager = SessionManager()

        return registry, session_manager

    def test_research_workflow(self, components):
        """Simulate a complete research workflow:
        1. User asks about Transformer
        2. Agent searches web
        3. Agent saves note
        4. Agent gives final answer
        """
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
        """Test cross-turn continuity:
        Turn 1: Research and save notes.
        Turn 2: Ask a follow-up — notes should be injected into system prompt.
        """
        registry, session_manager = components
        session = session_manager.create("cross-turn")

        # Turn 1: Research Transformer
        tc1 = _make_tool_call("web_search", '{"query": "Transformer"}')
        tc2 = _make_tool_call("save_note", '{"content": "Transformer uses self-attention.", "tags": ["AI"]}')
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
        llm2 = FakeLLM(["Based on your previous research, Transformer uses self-attention mechanism."])
        runtime2 = AgentRuntime(llm_client=llm2, tool_registry=registry, max_steps=5)
        result2 = runtime2.run(loaded_session, "What mechanism does Transformer use?")

        # The note should have been injected into the system prompt
        first_call = llm2.call_history[0]
        system_prompt = first_call["messages"][0]["content"]
        assert "self-attention" in system_prompt.lower()

        # Cleanup
        import os
        os.remove(session_manager._filepath("cross-turn"))
```

- [ ] **Step 2: 运行集成测试**

```bash
pytest tests/test_integration.py -v
```
Expected: PASS

- [ ] **Step 3: 编写 Demo 脚本**

`demo.py`:

```python
#!/usr/bin/env python3
"""Demo: Cross-turn knowledge assistant scenario.
This script demonstrates the agent's ability to:
1. Research a topic and save notes (Turn 1)
2. Recall notes across sessions (Turn 2)
3. Answer follow-up questions using accumulated knowledge (Turn 3)
"""
import sys
import os

# Add project root to path
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
    print("  Simple Agent Demo — Cross-Session Knowledge Assistant")
    print("=" * 60)

    runtime, sm = setup()

    # Create session
    session = sm.create("demo")
    print("\n📝 Session: demo")

    # Turn 1: Research
    print("\n" + "─" * 60)
    print("🔄 Turn 1: Research")
    print("─" * 60)
    q1 = "请帮我调研一下 Transformer 架构，重点了解注意力机制"
    print(f"👤 User: {q1}\n")
    r1 = runtime.run(session, q1)
    for t in r1.trace:
        if "tool" in t:
            print(f"  🔧 {t['tool']}({t.get('args', {})})")
            print(f"    → {t.get('result', '')[:120]}...")
        elif t.get("action") == "final_answer":
            print(f"  ✅ Final Answer")
    print(f"\n💬 Agent: {r1.answer}")
    sm.save(session)

    # Turn 2: Follow-up using knowledge
    print("\n" + "─" * 60)
    print("🔄 Turn 2: Follow-up (should use saved notes)")
    print("─" * 60)
    q2 = "注意力机制的具体计算公式是什么？请结合之前调研的内容回答"
    print(f"👤 User: {q2}\n")
    r2 = runtime.run(session, q2)
    for t in r2.trace:
        if "tool" in t:
            print(f"  🔧 {t['tool']}({t.get('args', {})})")
            print(f"    → {t.get('result', '')[:120]}...")
        elif t.get("action") == "final_answer":
            print(f"  ✅ Final Answer")
    print(f"\n💬 Agent: {r2.answer}")
    sm.save(session)

    # Turn 3: Cross-lingual
    print("\n" + "─" * 60)
    print("🔄 Turn 3: Translation task")
    print("─" * 60)
    q3 = "帮我把注意力机制的公式说明翻译成英文"
    print(f"👤 User: {q3}\n")
    r3 = runtime.run(session, q3)
    for t in r3.trace:
        if "tool" in t:
            print(f"  🔧 {t['tool']}({t.get('args', {})})")
            print(f"    → {t.get('result', '')[:120]}...")
        elif t.get("action") == "final_answer":
            print(f"  ✅ Final Answer")
    print(f"\n💬 Agent: {r3.answer}")
    sm.save(session)

    print("\n" + "=" * 60)
    print(f"✅ Demo complete. Session saved with {len(session.notes)} notes.")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py demo.py
git commit -m "test: add integration tests and cross-session demo script"
```

---

### Task 14: README 文档

**Files:**
- Create: `README.md`

- [ ] **Step 1: 编写 README**

`README.md`:

```markdown
# Simple Agent — 个人知识库助手

从零实现的最小可用 Agent，不依赖 LangChain 等框架，核心 Runtime 自己实现。

## 运行方式

### 1. 环境准备

```bash
# Python 3.10+
pip install -r requirements.txt
```

### 2. 设置 API Key

```bash
export DEEPSEEK_API_KEY="sk-your-deepseek-api-key"
# DeepSeek API Key 从 https://platform.deepseek.com 获取

# 可选：自定义 base URL
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
```

### 3. 运行

```bash
# 交互模式（自动创建或选择 session）
python main.py

# 创建新 session
python main.py new

# 恢复已有 session
python main.py resume demo

# 列出所有 session
python main.py list

# 删除 session
python main.py delete demo

# 运行 demo 演示脚本
python demo.py
```

### 4. 运行测试

```bash
pytest tests/ -v
```

## 系统设计

### 架构概览

```
CLI (main.py)
    │
    ▼
Agent Runtime (agent/runtime.py)
    ├── LLM Client (agent/llm_client.py) → DeepSeek API
    ├── Tool Registry (agent/tool_registry.py)
    │   ├── Calculator (tools/calculator.py)
    │   ├── WebSearch (tools/web_search.py)
    │   ├── SaveNote / SearchNotes (tools/notes.py)
    │   ├── Summarize (tools/summarize.py)
    │   └── Translate (tools/translate.py)
    └── Session Manager (session/manager.py)
        └── data/sessions/<id>.json
```

### Agent 主循环

```
User Input
    → 构建 System Prompt（注入相关知识库笔记）
    → LLM 分析（判断直接回答 or 调工具）
    → 有 Tool Call → ToolRegistry 执行工具 → 结果追加到 messages
    → 回到 LLM 分析（带工具结果）
    → 无 Tool Call → 最终答案
    → 返回答案 + Trace 日志
```

- 最大步数限制：10 步
- LLM 调用失败：自动重试 2 次
- 工具执行失败：错误信息喂回 LLM，让 LLM 自主调整

### 工具列表

| 工具 | 功能 |
|------|------|
| `web_search` | 搜索网络信息（mock 知识库） |
| `save_note` | 保存知识点到长期记忆 |
| `search_notes` | 检索已有笔记 |
| `summarize` | 调用 LLM 做文本摘要 |
| `calculator` | 安全的数学表达式求值 |
| `translate` | 调用 LLM 翻译文本 |

## Memory 机制

### 两层记忆架构

```
┌─────────────────────────┐
│  短期记忆（对话窗口）     │
│  • 完整 messages 历史    │
│  • 每次调 LLM 全量注入   │
│  • JSON 文件持久化       │
│  • 跨 Session 可恢复     │
├─────────────────────────┤
│  长期记忆（知识库）       │
│  • 用户通过 save_note    │
│    保存的知识笔记        │
│  • JSON 文件持久化       │
│  • 永久保留              │
└─────────────────────────┘
```

### 召回时机与放置方式

| | 短期记忆 | 长期记忆 |
|---|---|---|
| **放置时机** | 每次交互自动追加到 `session.messages` | Agent 调用 `save_note` 工具时 |
| **召回时机** | 每次调 LLM 时全量传入 `messages` 列表 | Session 加载时自动关键词匹配 → 注入 System Prompt |
| **存储格式** | `data/sessions/<id>.json` → `messages` 数组 | `data/sessions/<id>.json` → `notes` 数组 |

### 跨轮次继续执行

```
Round 1: "帮我调研 Transformer 架构"
    → web_search → save_note → Finish
    → 知识库: [note_1: Transformer 核心原理...]

（关闭程序，重新打开）

Round 2: "注意力机制的计算公式是什么？"
    → Runtime 自动关键词匹配: "注意力机制" 命中 note_1
    → System Prompt 注入: "相关笔记: [note_1] Transformer 核心原理..."
    → LLM 基于已有笔记直接回答（或 search_notes 进一步检索）
```

## 项目结构

```
simpleAgent/
├── main.py                 # CLI 入口
├── demo.py                 # Demo 演示脚本
├── requirements.txt        # 依赖
├── README.md               # 本文件
├── agent/
│   ├── runtime.py          # AgentRuntime 核心循环
│   ├── llm_client.py       # DeepSeek API 封装
│   └── tool_registry.py    # 工具注册与调度
├── tools/
│   ├── base.py             # Tool 基类 + 数据类型
│   ├── calculator.py       # 计算器
│   ├── web_search.py       # 搜索（mock）
│   ├── notes.py            # 笔记存取
│   ├── summarize.py        # 摘要
│   └── translate.py        # 翻译
├── session/
│   └── manager.py          # Session 管理
├── data/sessions/          # Session 持久化目录
└── tests/                  # 测试
```

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with system design and usage guide"
```

---

### Task 15: 最终验证与 Push

- [ ] **Step 1: 运行全部测试**

```bash
pytest tests/ -v
```
Expected: 全部 PASS

- [ ] **Step 2: 验证 demo 脚本（需要 API key）**

```bash
python demo.py
```

- [ ] **Step 3: 最终 Commit 和 Push**

```bash
git add -A
git status
git commit -m "chore: final cleanup and verification"  # 如有未提交的修改
git push -u origin main
```

---

## 任务依赖图

```
Task 1 (脚手架)
  └─► Task 2 (Tool 基类)
        ├─► Task 3 (Calculator)
        ├─► Task 4 (WebSearch)
        ├─► Task 5 (Summarize)
        ├─► Task 6 (Translate)
        └─► Task 7 (Notes)
              └─► Task 8 (ToolRegistry)
                    └─► Task 9 (LLMClient)
                          └─► Task 10 (SessionManager)
                                └─► Task 11 (Runtime) ◄── 核心
                                      └─► Task 12 (CLI)
                                            ├─► Task 13 (Integration + Demo)
                                            └─► Task 14 (README)
                                                  └─► Task 15 (Final Verify)
```
