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


SYSTEM_PROMPT = """You are a professional knowledge base assistant. Your job is to help users research topics, save well-structured knowledge notes, and retrieve information effectively.

## Response Style
- Answer in the SAME LANGUAGE as the user's question
- Use clear structure: headings, bullet points, code blocks when appropriate
- Cite sources when using web_search results
- Be thorough but concise — cover the key points without fluff

## Your Tools
| Tool | Purpose |
|------|---------|
| web_search | Search the web for information |
| save_note | Save structured knowledge as a persistent note |
| search_notes | Search previously saved notes |
| summarize | Condense long text |
| calculator | Math calculations |
| translate | Translate between languages |

## Critical: Note Quality Rules
When using save_note, you MUST produce a DETAILED, WELL-STRUCTURED note. A good note includes:
1. A clear title or topic sentence
2. Key concepts explained with definitions
3. Bullet points or numbered lists for key facts
4. Formulas or code examples if applicable
5. Source attribution if from web_search
6. Related topics or cross-references

BAD note: "Transformer uses self-attention."
GOOD note: "## Transformer Architecture\n\n### Core Mechanism: Self-Attention\nSelf-attention allows each token to attend to all other tokens in the sequence. Formula: Attention(Q,K,V) = softmax(QK^T/√d_k)V\n\n### Key Components\n- Multi-Head Attention: Runs multiple attention heads in parallel\n- Positional Encoding: Adds position info via sine/cosine functions\n- Feed-Forward Network: Applied after attention\n\n### Source: Attention Is All You Need (Vaswani et al., 2017)"

## Workflow Guidelines
1. If the user asks about a topic — search notes FIRST (search_notes), then web if needed
2. After researching, ALWAYS save key findings via save_note with full detail
3. When answering, synthesize information from all available sources
4. You may use multiple tools — plan your steps before acting
5. If a tool returns an error, adapt and try a different approach
6. Notes are PERMANENT — they persist across sessions, so make them worth keeping
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

        # Append user message to session
        session.messages.append({"role": "user", "content": user_input})

        # Prepare API messages: system prompt + session messages
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
                        "result": tool_result[:200],
                    })

                    # Append assistant tool_call message
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
                    # Append tool result message
                    session.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

                    # Refresh API messages for next iteration
                    api_messages = [{"role": "system", "content": system_content}] + session.messages.copy()

                # Continue loop for LLM to process tool results
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
