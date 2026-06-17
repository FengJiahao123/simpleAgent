from tools.base import Tool, Note, Session


class SaveNote(Tool):
    name = "save_note"
    description = "Save a piece of knowledge as a note for future reference. Notes persist across sessions."
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The knowledge content to save."
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for categorizing the note, e.g. ['AI', 'NLP']."
            },
            "source_url": {
                "type": "string",
                "description": "Optional source URL where the information came from."
            }
        },
        "required": ["content"]
    }

    def execute(self, content: str, tags: list | None = None, source_url: str = "", **kwargs) -> str:
        session: Session | None = kwargs.get("session")
        if session is None:
            return "Error: No session available to save the note. Please try again."

        note = Note(
            content=content,
            tags=tags if tags else [],
            source_url=source_url if source_url else None,
        )
        session.notes.append(note)
        tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
        return f"Note saved successfully (id: {note.id}){tags_str}"


class SearchNotes(Tool):
    name = "search_notes"
    description = "Search your existing notes for relevant knowledge. Use this before searching the web to leverage previously saved information."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords or question to search for in your notes."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str, **kwargs) -> str:
        session: Session | None = kwargs.get("session")
        if session is None:
            return "Error: No session available. Please try again."

        if not session.notes:
            return "You have no saved notes yet. Use web_search to find information, then save_note to keep it."

        query_lower = query.lower()
        scored: list[tuple[Note, int]] = []

        for note in session.notes:
            score = 0
            content_lower = note.content.lower()
            for word in query_lower.split():
                if word in content_lower:
                    score += 1
            for tag in note.tags:
                if tag.lower() in query_lower:
                    score += 2
            if score > 0:
                scored.append((note, score))

        if not scored:
            return f"No notes matched your query '{query}'. Try different keywords or use web_search."

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]

        output = f"Found {len(top)} matching note(s) for '{query}':\n\n"
        for i, (note, _score) in enumerate(top, 1):
            tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
            output += f"{i}.{tags_str} {note.content[:200]}\n"
            if note.source_url:
                output += f"   Source: {note.source_url}\n"
            output += "\n"
        return output.strip()
