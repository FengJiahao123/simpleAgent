import os
import time
from openai import OpenAI


class LLMClient:
    """Thin wrapper around OpenAI-compatible DeepSeek API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "deepseek-chat",
        max_retries: int = 2,
    ):
        self._api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY environment variable is required. "
                "Set it via `export DEEPSEEK_API_KEY=sk-...` or pass api_key= to LLMClient()."
            )

        self._base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self._model = model
        self._max_retries = max_retries

        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )

    def chat(self, messages: list[dict], tools: list[dict] | None = None):
        """Send messages to the LLM and return the response message object.

        Returns an object with:
          - .content: str | None
          - .tool_calls: list | None
        """
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                kwargs = {
                    "model": self._model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = self._client.chat.completions.create(**kwargs)
                return response.choices[0].message

            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    time.sleep(1 + attempt)
                else:
                    raise RuntimeError(
                        f"LLM API call failed after {self._max_retries + 1} attempts: {last_error}"
                    ) from last_error
