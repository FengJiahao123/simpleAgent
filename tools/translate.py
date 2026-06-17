from tools.base import Tool


class Translate(Tool):
    name = "translate"
    description = "Translate text from one language to another. Default target is English."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to translate."
            },
            "target_language": {
                "type": "string",
                "description": "The target language to translate to, e.g. 'Chinese', 'English', 'Japanese'. Default is 'English'."
            }
        },
        "required": ["text"]
    }

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def execute(self, text: str, target_language: str = "English", **kwargs) -> str:
        if self._llm_client is None:
            return f"[Translation to {target_language} unavailable — no LLM client configured]\nOriginal: {text}"

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a translator. Translate the user's text to {target_language}. "
                    f"Return only the translation, no preamble or explanation."
                ),
            },
            {"role": "user", "content": text},
        ]
        response = self._llm_client.chat(messages)
        return response.choices[0].message.content
