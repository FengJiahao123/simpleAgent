from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone


class Tool(ABC):
    """Base class for all tools. Each tool defines its interface via name,
    description, and parameters (JSON Schema)."""

    name: str = ""
    description: str = ""
    parameters: dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with the given arguments. Returns a string result.
        Extra kwargs (session, etc.) are silently ignored by tools that don't need them."""
        ...


@dataclass
class Note:
    """A knowledge note stored in the long-term memory."""
    content: str
    tags: list[str] = field(default_factory=list)
    source_url: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Session:
    """A conversation session with short-term and long-term memory."""
    session_id: str
    messages: list[dict] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
