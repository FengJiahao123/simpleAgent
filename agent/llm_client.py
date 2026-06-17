import os
import time
from openai import OpenAI


def _load_dotenv(dotenv_path: str = ".env") -> None:
    """Load .env file into os.environ (does not override existing vars)."""
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# Auto-load .env on import
_load_dotenv()


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
                "DEEPSEEK_API_KEY not found. Set it in one of these ways:\n"
                "  1. Create a .env file in the project root with: DEEPSEEK_API_KEY=sk-...\n"
                "  2. Set environment variable: $env:DEEPSEEK_API_KEY = 'sk-...'\n"
                "  3. Pass api_key= to LLMClient() directly."
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
