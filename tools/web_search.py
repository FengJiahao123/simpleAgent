import re
import requests
from bs4 import BeautifulSoup
from tools.base import Tool

# Fallback knowledge for when network is unavailable
_FALLBACK_KNOWLEDGE = {
    "transformer": [
        "Attention Is All You Need (Vaswani et al., 2017) — The original Transformer paper introducing self-attention mechanism.",
        "Transformer architecture: Encoder-decoder with Self-Attention. Multi-Head Attention with h parallel heads.",
    ],
    "deep learning": [
        "Deep Learning (Goodfellow, Bengio & Courville, 2016) — The definitive textbook on deep learning fundamentals.",
        "ResNet (He et al., 2015) — Residual connections enable training of very deep networks (152+ layers).",
    ],
    "react": [
        "ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2023) — Introduces ReAct paradigm where LLMs interleave reasoning traces with action steps.",
        "ReAct works by prompting the LLM to generate Thought-Action-Observation sequences. The model reasons, acts via tools, observes results, and continues until reaching a final answer.",
    ],
    "agent": [
        "LLM Agents: Autonomous agents powered by large language models that can plan, use tools, reflect on results, and complete multi-step tasks.",
        "Agent Architecture: Typically consists of Planner (break down tasks), Executor (call tools), and Memory (short-term + long-term).",
    ],
    "natural language processing": [
        "BERT (Devlin et al., 2018) — Bidirectional transformer pre-training for language understanding.",
        "GPT Series: GPT-3 (Brown et al., 2020) showed emergent few-shot learning. GPT-4 extended to multimodal.",
    ],
    "reinforcement learning": [
        "RLHF (Ouyang et al., 2022) — Aligning language models with human preferences via reinforcement learning.",
        "PPO (Schulman et al., 2017) — Proximal Policy Optimization, standard RL algorithm for LLM alignment.",
    ],
    "computer vision": [
        "ViT (Dosovitskiy et al., 2020) — Vision Transformer: apply self-attention to image patches.",
        "Stable Diffusion (Rombach et al., 2022) — Latent diffusion model for high-quality image generation.",
    ],
    "python": [
        "Python 3.12 Release Notes — New features: improved f-strings, type parameter syntax, perf improvements.",
        "Real Python Tutorials — Comprehensive guides on web dev, data science, automation with Python.",
    ],
    "database": [
        "PostgreSQL Documentation — ACID-compliant relational database with advanced features like JSONB and full-text search.",
        "MongoDB Manual — Document-oriented NoSQL database with flexible schema and aggregation pipeline.",
    ],
    "algorithm": [
        "Introduction to Algorithms (CLRS) — The standard textbook covering sorting, graph algorithms, dynamic programming, and NP-completeness.",
        "Algorithm Design Manual (Skiena) — Practical guide to algorithm design with real-world examples.",
    ],
    "linux": [
        "The Linux Programming Interface (Kerrisk) — Definitive guide to Linux/UNIX system programming.",
        "Linux Kernel Development (Love) — Deep dive into Linux kernel internals, process scheduling, and memory management.",
    ],
}


class WebSearch(Tool):
    name = "web_search"
    description = (
        "Search the web for real, up-to-date information via Baidu search engine. "
        "Returns titles, URLs, and snippets. Always cite source URLs in your response. "
        "Use this to find facts, articles, documentation, and current information."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Use concise keywords for best results."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> str:
        # 1. Try Baidu search (works well in China)
        try:
            result = self._baidu_search(query)
            if "[SOURCE:" in result and "0 found" not in result:
                return result
        except Exception:
            pass

        # 2. Fallback to local knowledge
        return self._fallback_search(query)

    def _baidu_search(self, query: str) -> str:
        url = "https://www.baidu.com/s"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = requests.get(url, params={"wd": query, "rn": 10}, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for container in soup.select(".result, .c-container"):
            title_el = container.select_one("h3 a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")

            # Collect snippet from multiple possible elements
            snippets = []
            for sel in [".c-abstract", ".c-span-last", "span"]:
                for el in container.select(sel):
                    txt = el.get_text(strip=True)
                    # Filter out noise
                    if len(txt) > 20 and txt != title and txt not in snippets:
                        snippets.append(txt)

            snippet = " | ".join(snippets[:2]) if snippets else ""

            if title and href:
                results.append({"title": title, "href": href, "body": snippet[:300]})

        if not results:
            return self._fallback_search(query)

        output = f"[SOURCE: Baidu Search] Results for '{query}' ({len(results)} found):\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. **{r['title']}**\n"
            if r["body"]:
                output += f"   {r['body'][:250]}\n"
            output += f"   URL: {r['href']}\n\n"
        return output.strip()

    def _fallback_search(self, query: str) -> str:
        """Local cache fallback when network is unavailable."""
        query_lower = query.lower().strip()
        results = []
        seen = set()

        # Exact match
        for keyword, entries in _FALLBACK_KNOWLEDGE.items():
            if keyword in query_lower:
                for entry in entries:
                    if entry not in seen:
                        results.append(entry)
                        seen.add(entry)

        # Partial match
        if not results:
            query_words = set(query_lower.split())
            for keyword, entries in _FALLBACK_KNOWLEDGE.items():
                kw_words = set(keyword.replace("-", " ").split())
                if query_words & kw_words or any(w in keyword for w in query_words):
                    for entry in entries:
                        if entry not in seen:
                            results.append(entry)
                            seen.add(entry)

        if not results:
            return (
                f"[SOURCE: No Results] Search for '{query}' returned no results — "
                f"network unavailable and topic not in local cache. "
                f"Please check your internet connection and try again."
            )

        output = f"[SOURCE: Local Cache (offline)] Results for '{query}':\n\n"
        for i, r in enumerate(results[:3], 1):
            output += f"{i}. {r}\n"
        return output.strip()
