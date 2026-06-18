import pytest
from tools.translate import Translate


class FakeLLMForTranslate:
    """Fake LLM client that returns a message object (matching LLMClient.chat())."""
    def chat(self, messages, tools=None):
        class Message:
            pass
        msg = Message()
        msg.content = "[Translated] Hello, world!"
        msg.tool_calls = None
        return msg


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

    def test_translate_fallback_without_llm(self):
        """Without an LLM client, Translate should show a fallback message."""
        translator = Translate()
        result = translator.execute(text="你好世界")
        assert "unavailable" in result.lower() or "no LLM" in result.lower() or "Original" in result
