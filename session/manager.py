import json
import os
import time
from tools.base import Session, Note


class SessionManager:
    """Manages session creation, persistence, and knowledge retrieval.

    Two-layer memory:
    - Short-term: session.messages (full conversation history, persisted to JSON)
    - Long-term: session.notes (knowledge base, persisted to JSON)
    """

    def __init__(self, data_dir: str = "data/sessions"):
        self._data_dir = data_dir
        os.makedirs(self._data_dir, exist_ok=True)

    def _filepath(self, session_id: str) -> str:
        return os.path.join(self._data_dir, f"{session_id}.json")

    def create(self, session_id: str) -> Session:
        """Create a new empty session."""
        return Session(session_id=session_id)

    def load(self, session_id: str) -> Session:
        """Load a session from disk. Raises FileNotFoundError if not found."""
        filepath = self._filepath(session_id)
        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Session '{session_id}' not found. Use 'create' first or check the ID."
            )

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session(
            session_id=data["session_id"],
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )

        # Restore notes
        for note_data in data.get("notes", []):
            note = Note(
                id=note_data.get("id", ""),
                content=note_data.get("content", ""),
                tags=note_data.get("tags", []),
                source_url=note_data.get("source_url"),
                created_at=note_data.get("created_at", ""),
            )
            session.notes.append(note)

        # Restore messages
        session.messages = data.get("messages", [])

        return session

    def save(self, session: Session) -> None:
        """Persist a session to disk."""
        session.updated_at = time.time()

        data = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "messages": session.messages,
            "notes": [
                {
                    "id": n.id,
                    "content": n.content,
                    "tags": n.tags,
                    "source_url": n.source_url,
                    "created_at": n.created_at,
                }
                for n in session.notes
            ],
        }

        filepath = self._filepath(session.session_id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_sessions(self) -> list[str]:
        """List all saved session IDs."""
        sessions = []
        if not os.path.exists(self._data_dir):
            return sessions
        for filename in os.listdir(self._data_dir):
            if filename.endswith(".json"):
                sessions.append(filename[:-5])
        return sorted(sessions)

    def get_related_notes(self, session: Session, query: str, top_k: int = 3) -> list[Note]:
        """Find notes relevant to the query using simple keyword matching.

        Called before each agent run to inject relevant knowledge into the system prompt.
        """
        if not session.notes or not query:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored: list[tuple[Note, int]] = []

        for note in session.notes:
            score = 0
            content_lower = note.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1
            for tag in note.tags:
                if tag.lower() in query_lower or tag.lower() in query_words:
                    score += 2
            if score > 0:
                scored.append((note, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [note for note, _ in scored[:top_k]]
