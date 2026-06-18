# AI Prompt 与问题解决记录

> 本项目使用 Claude Code (Claude Opus 4.8) 辅助开发。
> 记录主要的 AI 交互 Prompt、遇到的问题、及解决方案。

---

## 一、开发阶段总览

| 阶段 | 主要 AI Prompt | 产出 |
|------|---------------|------|
| 需求分析 | "从零实现一个最小可用 Agent，帮我分析怎么做，分成几步" | 设计文档 + 功能拆解 |
| 架构设计 | "方案一的 Runtime 和 ReAct 有什么区别？我自己写不也可以写成 ReAct 那种？" | 确认 ReAct + Function Calling 方案 |
| 实现计划 | "按照设计文档写一个完整的实现计划" | 15 个 Task 的 TDD 计划 |
| 逐任务实现 | "执行 Task 1 / Task 2 / ..." | 62 → 72 个单元测试全部通过 |
| 问题修复 | 见下方各问题解决记录 | — |

---

## 二、关键设计决策的 AI 对话

### Q1: 用什么语言？Python vs TypeScript？

**我的 Prompt**：无，AI 主动给了 A/B/C 选项。

**AI 建议**：Python（AI/LLM 生态最成熟，OpenAI SDK 支持最好）。

**我的决定**：Python ✅

---

### Q2: LLM API 选哪个？

**AI 选项**：OpenAI / Anthropic / 国产模型 / DeepSeek。

**我的决定**：DeepSeek V4 Pro（OpenAI 兼容接口，国内直接访问，tool calling 规范）。

---

### Q3: Session 存储方式？

**AI 选项**：纯内存 / JSON 文件 / SQLite / 内存+JSON 备份。

**我的决定**：D（内存运行时 + JSON 文件持久化），兼顾速度和可靠性。

---

### Q4: 工具选哪些？跨轮次场景做什么？

**脑暴过程**：

```
我的 Prompt: "你觉得做一个什么样的 agent 可以满足且有用？"

AI: 给了三个方案：
A - 个人知识库助手（搜索 → 保存笔记 → 检索）
B - 智能学习教练（出题 → 批改 → 追踪进度）
C - 私人项目管理助理（拆任务 → 追进度 → 记决策）

我的决定: A
```

---

### Q5: 短期记忆 vs 长期记忆？

**我的 Prompt**："比如你有没有处理短期记忆，长期记忆什么的"

**AI**：给了三层记忆设计（短期 + 摘要 + 长期）。

**我的反馈**："你觉得怎么样，有没有需要改进的？"

**AI**：
- 改进：长期记忆加关键词自动注入、短期记忆也持久化
- 砍掉：摘要记忆（DeepSeek 128K 上下文够用，不需要）

**我的决定**：两层（短期消息 + 长期笔记），摘除了摘要层。

---

### Q6: 搜索怎么实现？

**问题**：Mock 知识库数据太少，其他知识点搜不到。

**我的 Prompt**："除了 transformer 可以调研，其他的知识点我让他查他说无法在网上搜索到"

**AI 解决方案**：
1. 先试 DuckDuckGo → **被墙**（国内无法访问）
2. 再试 Bing 网页抓取 → **Bing 动态加载，抓不到结果**
3. 最终用 **百度搜索** + BeautifulSoup 网页解析 → 成功

**关键代码**：`tools/web_search.py` 中的 `_baidu_search()` 方法。

---

### Q7: 公式为什么乱码？

**问题**：笔记中的 `$$ \text{MultiHead}(Q,K,V) $$` 显示为原始文本，完全看不懂。

**我的 Prompt**："这些东西完全让人看不懂，能不能转化成那种公式而不是这种还得看半天才能看的"

**AI 解决方案**：前端引入 KaTeX（`katex.min.js` + `katex.min.css`），

**关键代码**：

```javascript
function renderLatex(html) {
  // $$...$$ → 块公式
  html.replace(/\$\$([\s\S]*?)\$\$/g, function(m, f) {
    return katex.renderToString(f.trim(), { displayMode: true });
  });
  // $...$ → 行内公式
  html.replace(/(?<!\$)\$(?!\$)([\s\S]*?)(?<!\$)\$(?!\$)/g, function(m, f) {
    return katex.renderToString(f.trim(), { displayMode: false });
  });
}
```

---

### Q8: 笔记不够详细？

**问题**：笔记内容太简单，格式差。

**我的 Prompt**："笔记我觉得并不详细，是不是提示词什么的没写好"

**AI 解决方案**：重写系统提示词，加入 Note Quality Rules：

```
BAD note: "Transformer uses self-attention."
GOOD note: "## Transformer Architecture\n\n### Core Mechanism: Self-Attention
  \nSelf-attention allows each token to attend to all other tokens...\n
  \n### Key Components\n- Multi-Head Attention\n- ..."
```

同时给 `save_note` 的 `content` 参数描述加上了 "Use Markdown formatting: ## headings, bullet points, ..."

---

### Q9: 笔记保存为 .md 文件？

**我的 Prompt**："我想这个保存笔记是一个 md 文件可以吗"

**AI 解决方案**：新增 `tools/export_doc.py`，支持 4 种格式（md / txt / docx / html），默认 md。

同时 `SaveNote.execute()` 执行后自动导出 `.md` 到 `data/notes/<session_id>/` 目录。

---

### Q10: 要终端还是要 Web 前端？

**我的 Prompt**："你这是自动就对话了？不能我手动对话吗，我希望稍微搞个前端吧"

**AI 解决方案**：加 Flask + HTML 前端。

- 后端：`web.py`（REST API：/chat, /sessions, /notes）
- 前端：`templates/index.html`（聊天界面 + Markdown 渲染 + trace 展示）
- 独立笔记页：`templates/notes.html`

---

### Q11: 如何识别搜索结果来源？

**我的 Prompt**："我怎么知道我问的知识点是否联网搜索了"

**AI 解决方案**：
- 搜索结果加 `[SOURCE: Baidu Search]` 标签
- 前端 trace 显示彩色 badge：🟢 WEB / 🟡 OFFLINE / 🔴 LLM

---

### Q12: API Key 怎么设置？

**我的 Prompt**："我在哪里设置 api"

**AI 解决方案**：`agent/llm_client.py` 启动时自动加载 `.env` 文件。

```python
def _load_dotenv(dotenv_path=".env"):
    # 读取 .env → os.environ（不覆盖已有变量）
```

用户只需在项目根目录的 `.env` 文件中填写 `DEEPSEEK_API_KEY=sk-...`。

---

## 三、开发中的 Bug 修复记录

| Bug | 原因 | 修复 |
|-----|------|------|
| 测试期望 `trace.length == 2`，实际是 3 | trace 包含 2 tool + 1 final_answer，测试写错了 | 修正断言为 `== 3` |
| `main.py list` 报 GBK 编码错误 | Windows 终端不支持 emoji | 替换所有 emoji 为纯文本标记 |
| CLI list/new/delete 需要 API Key | 不需要 LLM 的命令也调了 `LLMClient()` | 改为延迟初始化，list/new/delete 先执行 |
| `export_doc.execute()` 签名不匹配 | 加 `note_query` 参数后测试仍调旧签名 | 改用 `**kwargs` 模式接收所有参数 |

---

## 四、使用的 AI 工具

| 工具 | 用途 |
|------|------|
| Claude Code (Opus 4.8) | 全程辅助：需求分析 → 架构设计 → TDD 开发 → Bug 修复 → 文档 |
| Claude的思考过程 | 每次代码修改前分析影响范围、设计接口 |
| Claude的 subagent | 并行搜索、探索代码库 |

---

## 五、总结

整个开发过程是**人机协作**的典型模式：

1. **人做决策**：选 Python、选 DeepSeek、选两层记忆、选知识库场景
2. **AI 做执行**：写代码、写测试、修 Bug、生成文档
3. **人 Review**：每个阶段审设计、跑测试、提出改进意见
4. **迭代优化**：发现问题 → 提出 Prompt → AI 修复 → 验证 → 提交
