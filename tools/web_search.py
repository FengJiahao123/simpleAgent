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
