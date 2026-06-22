# Simple Agent — 个人知识库助手

不依赖 LangChain 等任何 Agent 框架，从零实现的最小可用 Agent。核心 Runtime（ReAct 循环）完全自己编写。

---

## 演示视频

[![Simple Agent 演示视频](https://img.shields.io/badge/Bilibili-演示视频-00A1D6?logo=bilibili)](https://b23.tv/qgW9kf6)

点击上方链接或访问：https://b23.tv/qgW9kf6

---

## 一、运行方式

### 1. 环境准备

```bash
# 要求 Python 3.10+
pip install -r requirements.txt
```

### 2. 配置 API Key

项目根目录下有 `.env` 文件，填入你的 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-你的Key
```

从 https://platform.deepseek.com 获取（注册后进入「API Keys」页面创建）。

### 3. 启动

**推荐：Web 界面**

```bash
python web.py
```

浏览器打开 `http://127.0.0.1:5000`，即可在可视化界面中对话。

Web 界面功能：
- 多 Session 管理（新建 / 切换 / 恢复）
- Markdown 实时渲染 + LaTeX 公式显示
- 工具调用 Trace（可折叠，带数据来源标签）
- 笔记浏览（独立页面 `http://127.0.0.1:5000/notes/<session_id>`）
- 对话历史自动持久化，关闭后重开可恢复

**备选：终端交互**

```bash
python main.py              # 交互模式（自动创建或选择 Session）
python main.py new          # 创建新 Session
python main.py resume <id>  # 恢复已有 Session
python main.py list         # 列出所有 Session
python main.py delete <id>  # 删除指定 Session
```

**Demo 演示**

```bash
python demo.py              # 自动执行三轮对话，展示跨轮次能力
```

### 4. 运行测试

```bash
pytest tests/ -v            # 72 个测试
```

---

## 二、系统设计

### 架构总览

```
Web UI (web.py + templates/)  ←── 推荐使用
CLI  (main.py)                 ←── 备选
    │
    ▼
Agent Runtime (agent/runtime.py)       ←── 核心 ReAct 循环（自实现）
    ├── LLM Client (agent/llm_client.py)     → DeepSeek API
    ├── Tool Registry (agent/tool_registry.py) → 工具注册与调度
    │   ├── web_search     → 百度真联网搜索
    │   ├── save_note      → 保存知识笔记（自动导出 .md）
    │   ├── search_notes   → 检索已有笔记
    │   ├── summarize      → LLM 摘要
    │   ├── calculator     → 安全数学计算
    │   ├── translate      → LLM 翻译
    │   └── export_doc     → 导出文档（md/docx/txt/html）
    └── Session Manager (session/manager.py)
        └── data/sessions/<id>.json  → 短期记忆 + 长期记忆
```

### Agent 主循环（ReAct 风格）

```
用户输入
  → 构造 System Prompt（自动注入相关笔记）
  → 调用 LLM（携带工具定义）
  → LLM 判断：直接回答？还是调用工具？
  → 有 tool_calls → ToolRegistry 执行工具 → 结果追加到对话 → 回到 LLM
  → 无 tool_calls → 最终答案
  → 返回答案 + Trace 日志 + 持久化 Session
```

**安全防护**：

| 机制 | 说明 |
|------|------|
| 最大步数限制 | `max_steps = 10`，防止死循环 |
| LLM 调用重试 | API 失败自动重试 2 次（间隔 1s / 2s） |
| 工具执行异常 | 捕获错误 → 将错误信息喂回 LLM → 让 LLM 自主调整策略 |
| Session 损坏 | 检测到损坏文件 → 新建 Session（不崩溃） |
| Ctrl+C 退出 | 自动保存 Session，不丢数据 |

### 工具列表（7 个）

| 工具 | 功能 | 特点 |
|------|------|------|
| `web_search` | 联网搜索 | 百度真实搜索，返回标题 + 摘要 + URL |
| `save_note` | 保存笔记 | 结构化 Markdown 笔记，自动导出 .md 文件 |
| `search_notes` | 检索笔记 | 关键词匹配，返回完整笔记内容 |
| `summarize` | 文本摘要 | 调用 LLM 摘要，无 LLM 时有提取式 fallback |
| `calculator` | 数学计算 | 白名单沙箱，防代码注入 |
| `translate` | 翻译 | 调用 LLM 翻译，无 LLM 时有 fallback |
| `export_doc` | 导出文档 | 支持 md（默认）/ docx / txt / html |

---

## 三、Memory 机制

### 两层记忆架构

```
┌──────────────────────────────┐
│  短期记忆（对话窗口）          │
│  · 完整 messages 历史          │
│  · 每次 LLM 调用全量注入       │
│  · JSON 文件持久化（跨 Session）│
└──────────────────────────────┘
┌──────────────────────────────┐
│  长期记忆（知识库）            │
│  · 用户通过 save_note 保存    │
│  · JSON 持久化 + .md 文件导出  │
│  · 永久保留，越用越聪明        │
└──────────────────────────────┘
```

### 召回时机与放置方式

| | 短期记忆 | 长期记忆（知识库笔记） |
|------|------|------|
| **放置什么** | 全部对话消息（用户/助手/工具调用结果） | 用户通过 save_note 保存的结构化知识点 |
| **放置时机** | 每次交互自动追加到 `session.messages` | Agent 调用 `save_note` 工具时 |
| **召回时机** | 每次调用 LLM 时全量传入上下文 | **被动注入**：每次新问题，Runtime 做关键词匹配 → 相关笔记自动注入 System Prompt；**主动检索**：Agent 可调用 `search_notes` 进一步查询 |
| **存储位置** | `data/sessions/<id>.json` → `messages` 字段 | `data/sessions/<id>.json` → `notes` 字段 + `data/notes/<id>/` 目录下的 .md 文件 |
| **跨 Session** | ✅ JSON 持久化，关闭程序后重新打开可恢复 | ✅ 永久保留 |

### 跨轮次继续执行

```
第 1 轮: "请帮我详细调研 Transformer 架构"
  → search_notes (空) → web_search → save_note → 最终回答
  → 知识库: [笔记1: "Transformer 核心原理与自注意力机制..."]

（关闭程序，重新打开）

第 2 轮: "注意力机制的计算公式是什么？"
  → Runtime 关键词匹配: "注意力机制" 命中笔记1
  → System Prompt 自动注入: "相关笔记: [笔记1] Transformer 核心原理..."
  → LLM 直接基于已有笔记回答（或调 search_notes 进一步检索）
  → 无需重新搜索，答案更精准
```

---

## 四、项目结构

```
simpleAgent/
├── web.py                  # Flask Web 服务（推荐启动方式）
├── main.py                 # CLI 终端入口（备选）
├── demo.py                 # Demo 演示脚本
├── requirements.txt        # 依赖列表
├── .env                    # API Key 配置（不上传 Git）
├── README.md               # 本文件
│
├── agent/                  # ═══ Agent 核心层 ═══
│   ├── runtime.py          # 🔥 AgentRuntime — ReAct 核心循环
│   ├── llm_client.py       # DeepSeek API 封装（含重试、.env 加载）
│   └── tool_registry.py    # 工具注册、定义生成、调度执行
│
├── tools/                  # ═══ 工具层（7 个工具）═══
│   ├── base.py             # Tool 抽象基类 + Note/Session 数据模型
│   ├── calculator.py       # 安全计算器（白名单沙箱）
│   ├── web_search.py       # 百度搜索引擎（requests + BeautifulSoup）
│   ├── notes.py            # save_note + search_notes（含 .md 导出）
│   ├── summarize.py        # LLM 摘要
│   ├── translate.py        # LLM 翻译
│   └── export_doc.py       # 导出为 md/docx/txt/html
│
├── session/                # ═══ 会话管理层 ═══
│   └── manager.py          # Session 创建/加载/保存 + 笔记检索
│
├── templates/              # ═══ Web 前端 ═══
│   ├── index.html          # 聊天界面（Markdown + KaTeX + Trace）
│   └── notes.html          # 独立笔记浏览页
│
├── data/                   # ═══ 持久化目录 ═══
│   ├── sessions/           # Session JSON 文件
│   ├── notes/              # 导出的 .md 笔记
│   └── exports/            # 导出的文档（docx/txt/html/md）
│
├── docs/superpowers/       # 设计文档
│   ├── specs/              # 设计规格说明书
│   └── plans/              # 实现计划（15 个 Task）
│
└── tests/                  # ═══ 测试（72 个）═══
    ├── test_tool_base.py         # 工具基类
    ├── test_calculator.py        # 计算器
    ├── test_web_search.py        # 搜索
    ├── test_notes.py             # 笔记存取
    ├── test_summarize.py         # 摘要
    ├── test_translate.py         # 翻译
    ├── test_tool_registry.py     # 工具注册
    ├── test_llm_client.py        # LLM 客户端
    ├── test_session_manager.py   # Session 管理
    ├── test_runtime.py           # 🔥 核心 Runtime
    ├── test_integration.py       # 集成测试（跨轮次）
    └── test_export_doc.py        # 文档导出
```

---

## 五、笔试题要求对照

| # | 题目要求 | 实现情况 |
|---|---------|---------|
| 1 | 支持多轮对话和 Session 维护 | ✅ Session 完整消息历史，JSON 持久化 |
| 2 | 不依赖现成 Agent 框架 | ✅ 零 LangChain/OpenHands 依赖，`agent/runtime.py` 自实现 |
| 3 | Agent 循环：接收输入→判断→调工具→执行→读结果→继续 | ✅ ReAct + Function Calling 循环 |
| 4 | 至少 3 个工具 | ✅ **7 个工具** |
| 5 | 最大步数限制 + 异常处理 + Trace 日志 | ✅ `max_steps=10`，LLM 重试，工具异常回传，每步 trace |
| 6 | 跨轮次继续执行 | ✅ Session 恢复 + 知识库关键词自动注入 |
| 7 | 真实 LLM API | ✅ DeepSeek V4 Pro（OpenAI 兼容接口） |

---

## 六、设计决策

- **不用 Agent 框架**：核心 `agent/runtime.py` 手动实现 ReAct 循环，零 LangChain 依赖
- **Function Calling 协议**：使用 DeepSeek 的 OpenAI 兼容 tool calling API，比手写文本解析更可靠
- **两层记忆**：短期记忆（对话消息）+ 长期记忆（知识笔记），均 JSON 持久化
- **关键词召回**：简单高效的关键词匹配做笔记注入，不需要向量数据库
- **百度真搜索**：DuckDuckGo 国内被墙 → Bing 动态加载 → 最终选用百度 + 网页解析
- **三级降级**：百度搜索 → 本地缓存（OFFLINE）→ 明确报错，保证任何情况下都有结果
- **`.env` 自动加载**：LLM Client 启动时自动读取项目根目录 `.env`，用户无需设置环境变量

---

## License

MIT
