from tools.base import Tool


class Summarize(Tool):
    name = "summarize"
    description = "Summarize a long text into a concise version. Useful for condensing search results or articles."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to summarize."
            },
            "max_length": {
                "type": "string",
                "description": "Optional maximum length of the summary in characters. Default is 200."
            }
        },
        "required": ["text"]
    }

    def __init__(self, llm_client=None):
        self._llm_client = llm_client

    def execute(self, text: str, max_length: str = "200", **kwargs) -> str:
        if self._llm_client is None:
            # Fallback: simple extractive summary (first N chars + last sentence)
            max_len = int(max_length) if max_length.isdigit() else 200
            if len(text) <= max_len:
                return text
            summary = text[:max_len].rsplit(".", 1)[0] + "."
            return f"[Summary] {summary}"

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a text summarizer. Summarize the given text in no more than "
                    f"{max_length} characters. Return only the summary, no preamble."
                ),
            },
            {"role": "user", "content": text},
        ]
        response = self._llm_client.chat(messages)
        return response.choices[0].message.content
