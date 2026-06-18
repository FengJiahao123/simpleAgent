from tools.base import Tool

# Fallback knowledge for when network is unavailable
_FALLBACK_KNOWLEDGE = {
    "transformer": [
        "Attention Is All You Need (Vaswani et al., 2017) — The original Transformer paper introducing self-attention mechanism.",
        "Transformer architecture: Encoder-decoder with Self-Attention. Formula: Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V. Multi-Head Attention with h parallel heads, d_k=d_model/h.",
        "The Illustrated Transformer by Jay Alammar — Visual explanation of Transformer internals.",
    ],
    "deep learning": [
        "Deep Learning (Goodfellow, Bengio & Courville, 2016) — The definitive textbook on deep learning fundamentals.",
        "Neural Networks: Layers of neurons with activation functions (ReLU, sigmoid). Training via backpropagation and gradient descent.",
        "ResNet (He et al., 2015) — Residual connections enable training of very deep networks (152+ layers).",
    ],
    "natural language processing": [
        "BERT (Devlin et al., 2018) — Bidirectional transformer pre-training for language understanding.",
        "GPT Series: GPT-3 (Brown et al., 2020) showed emergent few-shot learning. GPT-4 extended to multimodal.",
    ],
    "reinforcement learning": [
        "RLHF (Christiano et al., 2017 / Ouyang et al., 2022) — Aligning language models with human preferences.",
        "PPO (Schulman et al., 2017) — Proximal Policy Optimization, the standard RL algorithm for LLM alignment.",
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
        "PostgreSQL Documentation — ACID-compliant relational database with advanced features.",
        "MongoDB Manual — Document-oriented NoSQL database with flexible schema and aggregation pipeline.",
    ],
}


class WebSearch(Tool):
    name = "web_search"
    description = (
        "Search the web for REAL, up-to-date information. Returns titles, URLs, and snippets. "
        "This performs an actual internet search — use it to find facts, articles, documentation, "
        "and current information. Always cite the source URL in your response."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> str:
        # Try real search first
        try:
            return self._duckduckgo_search(query)
        except Exception:
            pass

        # Fallback to local knowledge
        return self._fallback_search(query)

    def _duckduckgo_search(self, query: str) -> str:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return self._fallback_search(query)

        output = f"[SOURCE: Real Web Search] Results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r.get('title', 'No title')}\n"
            output += f"   {r.get('body', '')[:300]}\n"
            output += f"   URL: {r.get('href', 'N/A')}\n\n"
        return output.strip()

    def _fallback_search(self, query: str) -> str:
        """Use local fallback knowledge if network is unavailable."""
        query_lower = query.lower().strip()
        results = []
        seen = set()

        for keyword, entries in _FALLBACK_KNOWLEDGE.items():
            if keyword in query_lower:
                for entry in entries:
                    if entry not in seen:
                        results.append(entry)
                        seen.add(entry)

        if not results:
            # Partial word match
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
                f"[SOURCE: LLM Knowledge] No results found for '{query}' — "
                f"network unavailable and topic not in local cache. "
                f"Answer from your training data and clearly tell the user this is not a live search result."
            )

        output = f"[SOURCE: Local Cache (offline)] Results for '{query}':\n\n"
        for i, r in enumerate(results[:3], 1):
            output += f"{i}. {r}\n"
        return output.strip()
