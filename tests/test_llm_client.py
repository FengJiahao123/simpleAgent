import os
import pytest
from agent.llm_client import LLMClient


class TestLLMClientInit:
    def test_uses_env_api_key(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        client = LLMClient()
        assert client._api_key == "sk-test-key"

    def test_uses_passed_api_key(self):
        client = LLMClient(api_key="sk-explicit")
        assert client._api_key == "sk-explicit"

    def test_default_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        client = LLMClient()
        assert "deepseek.com" in client._base_url

    def test_custom_base_url(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://custom.api.com")
        client = LLMClient()
        assert "custom.api.com" in client._base_url

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            LLMClient()


class TestLLMClientChat:
    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        return LLMClient()

    def test_chat_requires_api_key_or_mock(self, client):
        """Without a real API key or mock, chat() should raise a connection error."""
        messages = [{"role": "user", "content": "Hello"}]
        with pytest.raises(Exception):
            client.chat(messages)

    def test_message_format_preserved(self, client):
        """Verify the client doesn't mutate input messages."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        original = [m.copy() for m in messages]
        try:
            client.chat(messages)
        except Exception:
            pass
        assert messages == original
