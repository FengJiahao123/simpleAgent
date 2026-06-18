import pytest
from tools.summarize import Summarize


class FakeLLMForSummarize:
    """Fake LLM client that returns a message object (matching LLMClient.chat())."""
    def chat(self, messages, tools=None):
        class Message:
            pass
        msg = Message()
        msg.content = "This is a summarized version of the input text."
        msg.tool_calls = None
        return msg


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

    def test_summarize_fallback_without_llm(self):
        """Without an LLM client, Summarize should use extractive fallback."""
        summarizer = Summarize()
        result = summarizer.execute(text="This is a short text that does not need summarization.")
        assert isinstance(result, str)
        assert len(result) > 0
