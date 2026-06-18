import os
import re
from tools.base import Tool, Note, Session

EXPORTS_DIR = "data/exports"


def _ensure_exports_dir() -> str:
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    return EXPORTS_DIR


def _sanitize_filename(name: str, max_len: int = 50) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "", name).strip()
    return name[:max_len] if name else "export"


def _search_session_notes(session: Session | None, query: str):
    """Search session notes by keyword, return best match (or None)."""
    if not session or not session.notes:
        return None

    query_lower = query.lower()
    scored = []
    for note in session.notes:
        score = 0
        content_lower = note.content.lower()
        query_words = set(query_lower.split())
        for word in query_words:
            if word in content_lower:
                score += 1
        for tag in note.tags:
            if tag.lower() in query_lower or tag.lower() in query_words:
                score += 2
        if score > 0:
            scored.append((note, score))

    if not scored:
        return None
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


def _export_md(content: str, filepath: str) -> str:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def _export_txt(content: str, filepath: str) -> str:
    plain = content
    plain = re.sub(r"#{1,6}\s*", "", plain)
    plain = re.sub(r"\*\*(.+?)\*\*", r"\1", plain)
    plain = re.sub(r"\*(.+?)\*", r"\1", plain)
    plain = re.sub(r"`{1,3}[^`]*`{1,3}", "", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(plain)
    return filepath


def _export_docx(content: str, filepath: str) -> str:
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.styles["Normal"].font.size = Pt(11)
    for line in content.split("\n"):
        line = line.rstrip()
        if not line:
            doc.add_paragraph("")
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], style="List Bullet")
        elif re.match(r"^\d+\.\s", line):
            doc.add_paragraph(re.sub(r"^\d+\.\s", "", line), style="List Number")
        elif line.startswith("> "):
            doc.add_paragraph(line[2:], style="Quote")
        else:
            p = doc.add_paragraph()
            parts = re.split(r"(\*\*.*?\*\*|\*.*?\*|`.*?`)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    run = p.add_run(part[2:-2])
                    run.bold = True
                elif part.startswith("*") and part.endswith("*") and not part.startswith("**"):
                    run = p.add_run(part[1:-1])
                    run.italic = True
                elif part.startswith("`") and part.endswith("`"):
                    run = p.add_run(part[1:-1])
                    run.font.name = "Consolas"
                else:
                    p.add_run(part)
    doc.save(filepath)
    return filepath


def _export_html(content: str, filepath: str) -> str:
    html = content
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)
    html = html.replace("\n", "<br>\n")

    full = "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head><meta charset=\"UTF-8\">"
    full += "<title>Exported Document</title>\n<style>\n"
    full += "body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.7; color: #333; }\n"
    full += "h1 { color: #c0392b; border-bottom: 2px solid #c0392b; padding-bottom: 8px; }\n"
    full += "h2 { color: #2c3e50; margin-top: 24px; }\n"
    full += "h3 { color: #555; }\n"
    full += "code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }\n"
    full += "strong { color: #c0392b; }\n"
    full += "a { color: #2980b9; }\n"
    full += "</style></head>\n<body>\n" + html + "\n</body></html>"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full)
    return filepath


EXPORTERS = {
    "md": ("Markdown", _export_md),
    "txt": ("Plain Text", _export_txt),
    "docx": ("Word Document", _export_docx),
    "html": ("HTML Page", _export_html),
}


class ExportDoc(Tool):
    name = "export_doc"
    description = (
        "Export content as a file. Two ways to use it:\n"
        "1. Pass 'note_query' to automatically find and export a specific note from your knowledge base. "
        "Example: export_doc(note_query='Transformer', format='md') exports the note about Transformer.\n"
        "2. Pass 'content' directly to export arbitrary text.\n"
        "Supports: md (Markdown, default), txt (Plain Text), docx (Word), html (Web page).\n"
        "When the user says 'export the Transformer note', use note_query='Transformer' — "
        "this will search notes, find the right one, and export it with full content."
    )
    parameters = {
        "type": "object",
        "properties": {
            "note_query": {
                "type": "string",
                "description": (
                    "Keywords to find a saved note. The tool searches all notes, picks the best match, "
                    "and exports its FULL content. "
                    "Use when user says 'export the Transformer note' or 'save that as Word'."
                )
            },
            "content": {
                "type": "string",
                "description": "Raw content to export. Only use if note_query doesn't apply."
            },
            "filename": {
                "type": "string",
                "description": "Base filename without extension. Auto-generated if not provided."
            },
            "format": {
                "type": "string",
                "enum": ["md", "txt", "docx", "html"],
                "description": "Output format. Default: 'md'."
            }
        },
        "required": []
    }

    def execute(self, **kwargs) -> str:
        note_query = str(kwargs.get("note_query", "") or "")
        content = str(kwargs.get("content", "") or "")
        filename = str(kwargs.get("filename", "") or "")
        format = str(kwargs.get("format", "") or "md")
        session: Session | None = kwargs.get("session")

        fmt = format.lower()
        if fmt not in EXPORTERS:
            return (
                f"Unsupported format: '{format}'. "
                f"Available formats: {', '.join(EXPORTERS.keys())}"
            )

        label, exporter_fn = EXPORTERS[fmt]

        # Mode A: Export by note query
        if note_query:
            note = _search_session_notes(session, note_query)
            if note is None:
                note_list = ""
                if session and session.notes:
                    note_list = "\nAvailable: " + ", ".join(
                        n.id + " - " + n.content[:60] for n in session.notes
                    )
                return f"No note matched '{note_query}'." + note_list
            content = note.content
            if not filename:
                first_line = content.split("\n")[0].strip().lstrip("#").strip()
                filename = _sanitize_filename(first_line) if first_line else f"note-{note.id}"

        # Mode B: Direct content
        if not content:
            return (
                "Error: provide either 'note_query' (to export a saved note by keyword) "
                "or 'content' (raw text to export).\n"
                "Example: export_doc(note_query='Transformer', format='md')"
            )

        if not filename:
            first_line = content.split("\n")[0].strip().lstrip("#").strip()
            filename = _sanitize_filename(first_line) if first_line else "export"

        filepath = os.path.join(_ensure_exports_dir(), f"{filename}.{fmt}")
        exporter_fn(content, filepath)

        return (
            f"Document exported successfully!\n"
            f"  Format: {label} (.{fmt})\n"
            f"  File: {filepath}\n"
            f"  Size: {os.path.getsize(filepath)} bytes"
        )
