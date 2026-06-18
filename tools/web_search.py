from tools.base import Tool

# Mock knowledge base
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
        "Transformer architecture: Encoder-decoder structure. Self-Attention formula: Attention(Q,K,V) = softmax(QK^T/sqrt(d_k))V. Multi-Head Attention runs h parallel attention heads, each with dimension d_k = d_model/h. Positional Encoding uses sine/cosine functions. Layer Normalization and Residual Connections after each sub-layer.",
        "The Illustrated Transformer by Jay Alammar — Visual guide explaining Transformer architecture step by step.",
    ],
    "attention": [
        "Self-Attention mechanism: Given input sequence X, compute Query=W_Q·X, Key=W_K·X, Value=W_V·X. Output is weighted sum of Values, weights determined by softmax(QK^T / sqrt(d_k)). Multiple heads capture different subspace relationships.",
        "Multi-Head Attention: Concat(head_1, ..., head_h)W_O where each head_i = Attention(Q·W_i^Q, K·W_i^K, V·W_i^V). Typical values: h=8, d_k=d_model/h=64.",
        "FlashAttention (Dao et al., 2022) — IO-aware attention algorithm achieving 2-4x speedup by reducing memory reads/writes.",
    ],
    "deep learning": [
        "Neural Networks: Layers of neurons with activation functions (ReLU, sigmoid, tanh). Training via backpropagation and gradient descent.",
        "CNN (Convolutional Neural Networks): Specialized for grid-like data. Uses convolution, pooling, and fully-connected layers. Key architectures: ResNet, VGG, Inception.",
        "RNN/LSTM/GRU: Recurrent architectures for sequential data. LSTM uses forget/input/output gates to control information flow. GRU is a simplified variant with 2 gates.",
    ],
    "web development": [
        "MDN Web Docs — Mozilla's comprehensive reference for HTML, CSS, and JavaScript APIs.",
        "React Official Documentation — Guides for building user interfaces with React components and hooks.",
        "Flask Web Framework — Lightweight Python web framework for building APIs and web applications.",
    ],
    "deepseek": [
        "DeepSeek-V3 — A strong Mixture-of-Experts (MoE) language model with 671B total parameters, 37B activated per token. Supports 128K context window.",
        "DeepSeek-R1 — Reasoning model that uses reinforcement learning to improve chain-of-thought reasoning capabilities.",
    ],
    "language model": [
        "Large Language Models (LLMs): Transformer-based models trained on massive text corpora. Key examples: GPT-4, Claude, DeepSeek, LLaMA, Gemini.",
        "LLM Training Process: Pre-training (next-token prediction on web-scale data) → Supervised Fine-Tuning (instruction following) → RLHF/DPO (alignment with human preferences).",
        "Scaling Laws: Model performance improves predictably with more compute, data, and parameters (Kaplan et al., 2020; Chinchilla, 2022).",
    ],
    "reinforcement learning": [
        "Reinforcement Learning: Agent learns by interacting with environment, receiving rewards for good actions. Key concepts: state, action, reward, policy, value function.",
        "RLHF (Reinforcement Learning from Human Feedback): Train a reward model from human preference data, then optimize LLM policy via PPO against the reward model.",
        "Key Algorithms: Q-Learning, Policy Gradient, Actor-Critic (A2C/A3C), PPO, DQN, SAC.",
    ],
    "natural language processing": [
        "NLP Pipeline: Tokenization → Embedding → Encoding → Task-specific head. Modern approach uses pre-trained Transformer models fine-tuned for downstream tasks.",
        "Key NLP Tasks: Text classification, named entity recognition (NER), question answering, machine translation, summarization, sentiment analysis.",
        "Word Embeddings: Word2Vec, GloVe. Modern contextual embeddings: BERT, GPT generate different embeddings for the same word based on context.",
    ],
    "computer vision": [
        "Image Classification: Assign labels to images. Key models: ResNet (residual connections for deep networks), ViT (Vision Transformer applies self-attention to image patches).",
        "Object Detection: Locate and classify objects in images. YOLO, Faster R-CNN, DETR are popular architectures.",
        "Image Generation: Stable Diffusion (latent diffusion model), DALL-E, Midjourney. GANs (Generative Adversarial Networks) use generator-discriminator architecture.",
    ],
    "database": [
        "SQL Databases: Relational databases using Structured Query Language. ACID properties (Atomicity, Consistency, Isolation, Durability). Examples: PostgreSQL, MySQL.",
        "NoSQL Databases: Non-relational databases for flexible schemas. Types: Document (MongoDB), Key-Value (Redis), Column-family (Cassandra), Graph (Neo4j).",
        "Database Indexing: B-Tree indexes speed up queries. Trade-off: faster reads vs slower writes and more storage.",
    ],
    "operating system": [
        "Process vs Thread: Process is an independent execution unit with its own memory space. Threads share memory within a process. Context switching has overhead.",
        "Memory Management: Virtual memory maps virtual addresses to physical memory. Paging divides memory into fixed-size pages. Page faults trigger loading from disk.",
        "File Systems: Organize and store data on disk. Common types: NTFS (Windows), ext4 (Linux), APFS (macOS).",
    ],
    "algorithm": [
        "Sorting Algorithms: QuickSort (average O(n log n), worst O(n^2)), MergeSort (stable O(n log n)), HeapSort (in-place O(n log n)).",
        "Graph Algorithms: Dijkstra (shortest path), BFS/DFS (traversal), A* (heuristic search), Kruskal/Prim (minimum spanning tree).",
        "Dynamic Programming: Break problem into overlapping subproblems, cache results. Examples: Fibonacci, Knapsack, Edit Distance, Longest Common Subsequence.",
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

        # 1. Exact keyword match
        for keyword, entries in _MOCK_KNOWLEDGE.items():
            if keyword in query_lower:
                for entry in entries:
                    if entry not in seen:
                        results.append(entry)
                        seen.add(entry)

        # 2. If no exact match, try partial word match
        if not results:
            query_words = set(query_lower.split())
            for keyword, entries in _MOCK_KNOWLEDGE.items():
                kw_words = set(keyword.replace("-", " ").split())
                if query_words & kw_words or any(w in keyword for w in query_words):
                    for entry in entries:
                        if entry not in seen:
                            results.append(entry)
                            seen.add(entry)

        # 3. Fallback: LLM must use its own training knowledge
        if not results:
            return (
                f"[SOURCE: LLM Knowledge] The search engine did not find '{query}' in the local index. "
                f"You MUST answer from your own training data. "
                f"IMPORTANT: Clearly tell the user this response comes from your training knowledge (not a live search), "
                f"and suggest trying different search keywords or saving findings with save_note for future reference."
            )

        output = f"[SOURCE: Local Database] Results for '{query}' (found {len(results[:3])} entries):\n\n"
        for i, result in enumerate(results[:3], 1):
            output += f"{i}. {result}\n"
        return output.strip()
