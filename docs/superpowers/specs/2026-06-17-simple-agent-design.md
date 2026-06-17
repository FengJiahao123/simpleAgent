# Simple Agent — 设计规格说明书

> 日期：2026-06-17
> 项目：从零实现一个最小可用 Agent（面试笔试题）
> 语言：Python 3.10+
> LLM：DeepSeek V4 Pro（OpenAI 兼容接口）

---

## 1. 项目概述

### 1.1 目标

从零实现一个**个人知识库助手 Agent**，不依赖 LangChain 等现成框架，核心 Runtime 自己编写。

### 1.2 核心能力

- 理解用户问题，自主决定直接回答还是调用工具
- 搜索信息 → 保存知识 → 检索知识 → 综合回答
- 支持多轮对话，Session 可跨程序重启恢复
- 用户积累的知识笔记跨 Session 永久保留

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────┐
│                    CLI 入口                       │
│              python main.py [command]             │
├──────────────────────────────────────────────────┤
│                 Agent Runtime                     │
│   • ReAct-style 主循环                            │
│   • 步数限制 (max_steps=10)                       │
│   • 异常处理 + 兜底                               │
│   • 执行日志 (step trace)                         │
├──────────────────┬───────────────────────────────┤
│   LLM Client     │      Tool Registry            │
│   DeepSeek API   │  注册 · 匹配 · 执行 · 日志    │
├──────────────────┴───────────────────────────────┤
│              Session Manager                      │
│   • 创建 / 加载 / 保存 Session                    │
│   • 短期记忆：全量 messages，JSON 文件持久化       │
│   • 长期记忆：知识库 notes，JSON 文件持久化        │
│   • 自动关键词召回：加载时匹配相关笔记注入 prompt   │
├──────────────────────────────────────────────────┤
│                   Tool 层                         │
│  web_search │ save_note │ search_notes            │
│  summarize  │ calculator │ translate              │
└──────────────────────────────────────────────────┘
```

---

## 3. 模块设计

### 3.1 Agent Runtime（`agent/runtime.py`）

核心 ReAct 循环，职责：

1. 接收用户输入
2. 构造 messages（system prompt + 历史消息 + 用户输入 + 自动注入的相关笔记）
3. 调用 LLM（带 tool definitions）
4. 解析 LLM 响应：
   - 有 `tool_calls`：通过 ToolRegistry 执行工具，记录 trace，结果追加到 messages，回到步骤 3
   - 无 `tool_calls`（content）：视为最终答案，结束循环
5. 步数达到 `max_steps`：强制结束，返回已有内容
6. 异常处理：捕获 LLM 调用失败、工具执行失败，记录错误并尝试恢复

```python
class AgentRuntime:
    max_steps: int = 10

    def run(self, session: Session, user_input: str) -> AgentResult:
        """执行一次 Agent 循环，返回最终答案 + trace"""
        ...
```

### 3.2 LLM Client（`agent/llm_client.py`）

封装 DeepSeek API 调用：

- 使用 OpenAI 兼容 SDK（`openai` 库，指向 DeepSeek endpoint）
- 支持 function calling（tool definitions 自动转换）
- 处理 API 错误（超时、限流、格式异常）

```python
class LLMClient:
    def chat(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        """发送消息给 LLM，返回响应（content + tool_calls）"""
        ...
```

### 3.3 Tool Registry（`agent/tool_registry.py`）

工具注册与调度：

- 每个工具是一个类，实现 `name`、`description`、`parameters`（JSON Schema）、`execute(args)` 方法
- Registry 维护 `dict[name → Tool]` 映射
- 提供 `get_definitions()` 生成 function calling 格式的工具定义列表
- 提供 `execute(name, args)` 执行工具并返回结果字符串

```python
class ToolRegistry:
    def register(self, tool: Tool): ...
    def get_definitions(self) -> list[dict]: ...
    def execute(self, name: str, args: dict) -> str: ...
```

### 3.4 Session Manager（`session/manager.py`）

两层记忆管理：

**短期记忆（对话窗口）**：
- `Session.messages: list[dict]` — 完整对话历史（user/assistant/tool）
- 每次交互自动追加
- 调用 LLM 时全量注入
- 持久化到 `data/sessions/<session_id>.json`

**长期记忆（知识库）**：
- `Session.notes: list[Note]` — 用户通过 `save_note` 保存的知识点
- `Note` 结构：`{id, content, tags, source_url, created_at}`
- 召回机制：
  - **被动注入**：Session 加载时，Runtime 做关键词匹配，将相关笔记注入 system prompt
  - **主动检索**：Agent 可调用 `search_notes` 工具主动查询知识库

```python
@dataclass
class Note:
    id: str
    content: str
    tags: list[str]
    source_url: str | None
    created_at: str

@dataclass
class Session:
    session_id: str
    messages: list[dict]       # 短期记忆
    notes: list[Note]           # 长期记忆
    created_at: float
    updated_at: float

class SessionManager:
    def create(self, session_id: str) -> Session: ...
    def load(self, session_id: str) -> Session: ...
    def save(self, session: Session): ...
    def list_sessions(self) -> list[str]: ...
    def get_related_notes(self, session: Session, query: str, top_k: int = 3) -> list[Note]: ...
```

### 3.5 工具层（`tools/`）

| 工具 | 文件 | 说明 |
|------|------|------|
| `web_search` | `tools/web_search.py` | 网络搜索，初期 mock 返回预设结果，可后续接入真实 API |
| `save_note` | `tools/notes.py` | 保存知识点到知识库 |
| `search_notes` | `tools/notes.py` | 搜索已有笔记（关键词 + 简单语义匹配） |
| `summarize` | `tools/summarize.py` | 调用 LLM 做文本摘要 |
| `calculator` | `tools/calculator.py` | 安全的数学表达式求值 |
| `translate` | `tools/translate.py` | 调用 LLM 翻译文本 |

---

## 4. 数据流

### 4.1 单次交互流程

```
User: "帮我调研 Transformer 架构"
    │
    ▼
SessionManager.load("demo-001")
    │ 加载 messages[] + notes[]
    ▼
Runtime.get_related_notes(session, query="Transformer 架构")
    │ 关键词匹配 notes → 找到 0 条相关笔记
    ▼
Runtime.run(session, user_input)
    │
    ▼ messages = [system_prompt, ...history, user_msg]
LLMClient.chat(messages, tools=[web_search, save_note, ...])
    │
    ▼ response.tool_calls = [{name: "web_search", args: {query: "Transformer 架构"}}]
ToolRegistry.execute("web_search", {query: "Transformer 架构"})
    │ 返回搜索结果
    ▼ messages.append(tool_result)
LLMClient.chat(messages, tools=[...])
    │
    ▼ response.tool_calls = [{name: "save_note", args: {content: "Transformer...", tags: ["AI"]}}]
ToolRegistry.execute("save_note", ...)
    │ note 写入 session.notes
    ▼ messages.append(tool_result)
LLMClient.chat(messages, tools=[...])
    │
    ▼ response.content = "已为你整理并保存 Transformer 架构的笔记"
    │ 无 tool_calls → 最终答案
    ▼
SessionManager.save(session)
    │ 持久化 messages + notes 到 JSON
    ▼
输出: trace + final_answer
```

### 4.2 跨轮次流程

```
启动程序 → load session "demo-001"
    │
    ▼ messages = [上次对话的完整历史]
    ▼ notes = [note_1: "Transformer 核心原理..."]
    │
User: "注意力机制怎么算的？"
    │
    ▼ Runtime 做关键词匹配: "注意力" → 命中 note_1
    ▼ system_prompt 自动追加:
    │   "你可能相关的历史笔记：
    │    [笔记1] Transformer 核心原理：Self-Attention 计算公式为..."
    │
    ▼ LLM 看到这段 → 可以直接回答，或调用 search_notes 查更多
    │
    ▼ 最终答案基于已有笔记 + 必要时补充搜索
```

---

## 5. 错误处理

| 异常场景 | 处理策略 |
|----------|----------|
| LLM API 调用失败 | 重试 2 次（间隔 1s/2s），失败后返回友好错误信息 |
| LLM 返回格式异常 | 尝试兜底解析，解析失败则记录 trace 并返回原始输出 |
| 工具执行失败 | 捕获异常，将错误信息作为 Observation 喂回 LLM，让它调整 |
| 达到 max_steps | 强制结束，让 LLM 基于已有信息给出最终答案 |
| Session 文件损坏 | 备份原文件，新建 session |
| 用户 Ctrl+C 中断 | 优雅退出，自动 save session |

---

## 6. Trace / 日志格式

```
┌─ Agent Trace ──────────────────────────────────┐
│ Session: demo-001                               │
│ User Input: 帮我调研 Transformer 架构             │
│                                                  │
│ [Step 1/10] 🔧 web_search                       │
│   Args: {"query": "Transformer 架构"}             │
│   Result: 找到 3 条相关结果...                    │
│   Token: 1250                                    │
│                                                  │
│ [Step 2/10] 🔧 save_note                         │
│   Args: {"content": "Transformer 是一种...", ...}  │
│   Result: 笔记已保存 (note_id: abc123)            │
│   Token: 890                                     │
│                                                  │
│ [Step 3/10] ✅ Final Answer                      │
│   已为你整理 Transformer 架构的核心知识点...       │
│   Total Token: 3240                              │
└──────────────────────────────────────────────────┘
```

---

## 7. CLI 设计

```bash
# 新建会话
python main.py new

# 继续已有会话
python main.py resume <session_id>

# 列出所有会话
python main.py list

# 删除会话
python main.py delete <session_id>

# 进入交互模式（默认行为）
python main.py
```

交互模式下：
```
🤖 Simple Agent > 帮我调研一下 Transformer 架构

[Step 1/10] 🔧 web_search(query="Transformer 架构") → 3 条结果
[Step 2/10] 🔧 save_note(content="Transformer...") → 已保存
[Step 3/10] ✅ 已为你整理并保存笔记。

🤖 Simple Agent > 注意力机制怎么算的？
...
```

---

## 8. 记忆机制总结（README 必需内容）

| | 短期记忆 | 长期记忆 |
|---|---|---|
| **内容** | 全部对话消息（user/assistant/tool） | 用户通过 save_note 保存的知识笔记 |
| **放置时机** | 每次交互自动追加 | Agent 调用 `save_note` 工具时 |
| **召回时机** | 每次调用 LLM 全量传入上下文 | 关键词匹配自动注入 system prompt + Agent 主动调用 `search_notes` |
| **存储位置** | `data/sessions/<id>.json` → `messages` 字段 | `data/sessions/<id>.json` → `notes` 字段 |
| **跨 Session** | ✅ 可恢复（JSON 持久化） | ✅ 永久保留 |
| **容量管理** | DeepSeek 128K 上下文窗口内全量传入 | 关键词匹配取 top-k 注入，Agent 可按需检索更多 |

---

## 9. 开发环境

- Python 3.10+
- `openai>=1.0.0`（指向 DeepSeek endpoint）
- `pytest`（测试）
- 无其他第三方 Agent 框架依赖
