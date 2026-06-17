import os
import re
from tools.base import Tool, Note, Session


# Directory for exported .md note files
NOTES_DIR = "data/notes"


def _ensure_notes_dir(session_id: str = "") -> str:
    """Ensure the notes directory exists, optionally scoped to a session."""
    path = os.path.join(NOTES_DIR, session_id) if session_id else NOTES_DIR
    os.makedirs(path, exist_ok=True)
    return path


def _note_to_markdown(note: Note) -> str:
    """Convert a Note to a well-formatted Markdown string."""
    lines = []
    tags_str = ", ".join(note.tags) if note.tags else "None"
    lines.append(f"---")
    lines.append(f"id: {note.id}")
    lines.append(f"tags: [{tags_str}]")
    lines.append(f"created: {note.created_at}")
    if note.source_url:
        lines.append(f"source: {note.source_url}")
    lines.append(f"---")
    lines.append("")
    lines.append(note.content)
    return "\n".join(lines)


def _sanitize_filename(text: str, max_len: int = 60) -> str:
    """Create a safe filename from note content."""
    # Take first line or first N chars
    first_line = text.split("\n")[0].strip()
    if first_line.startswith("#"):
        first_line = first_line.lstrip("#").strip()
    # Remove special characters
    name = re.sub(r'[<>:"/\\|?*]', '', first_line)
    name = name.strip()[:max_len] if name else "note"
    return name


def export_note_to_md(note: Note, session_id: str) -> str:
    """Export a single note as a .md file. Returns the file path."""
    dir_path = _ensure_notes_dir(session_id)
    safe_name = _sanitize_filename(note.content)
    filename = f"{note.id}-{safe_name}.md"
    filepath = os.path.join(dir_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(_note_to_markdown(note))
    return filepath


def export_all_notes_to_md(session) -> str:
    """Export all notes in a session as .md files. Returns the directory path."""
    dir_path = _ensure_notes_dir(session.session_id)
    for note in session.notes:
        export_note_to_md(note, session.session_id)
    return dir_path


class SaveNote(Tool):
    name = "save_note"
    description = (
        "Save a piece of knowledge as a structured note for future reference. "
        "Notes persist across sessions and are exported as Markdown files. "
        "Make the content DETAILED and WELL-STRUCTURED — include headings, lists, "
        "definitions, formulas, examples, and source attribution where applicable. "
        "A good note should be useful even months later."
    )
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": (
                    "The full knowledge content to save. Use Markdown formatting: "
                    "## headings, bullet points, numbered lists, **bold**, code blocks, etc. "
                    "Include definitions, formulas, examples, and source attribution."
                )
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for categorizing, e.g. ['AI', 'NLP', 'transformer']. Use lowercase."
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

        # Export to .md file
        try:
            md_path = export_note_to_md(note, session.session_id)
        except Exception:
            md_path = "(file export failed)"

        tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
        return (
            f"Note saved successfully!\n"
            f"  ID: {note.id}\n"
            f"  Tags: {tags_str}\n"
            f"  MD file: {md_path}\n"
            f"  Content preview: {content[:150]}..."
        )


class SearchNotes(Tool):
    name = "search_notes"
    description = (
        "Search previously saved notes for relevant knowledge. "
        "ALWAYS search notes first before using web_search — your notes contain curated, "
        "detailed information that is often better than raw web results."
    )
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
        top = scored[:3]

        output = f"Found {len(top)} matching note(s) for '{query}':\n\n"
        for i, (note, _score) in enumerate(top, 1):
            tags_str = f" [{', '.join(note.tags)}]" if note.tags else ""
            # Show more content since notes are now detailed
            output += f"{i}.{tags_str}\n{note.content[:500]}\n"
            if note.source_url:
                output += f"   Source: {note.source_url}\n"
            output += "\n"
        return output.strip()
