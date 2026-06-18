import os
import pytest
from tools.export_doc import ExportDoc
from tools.base import Session, Note


class TestExportDoc:
    @pytest.fixture
    def exporter(self):
        return ExportDoc()

    def test_export_md(self, exporter):
        content = "## Hello\n\nThis is a test."
        result = exporter.execute(content=content, filename="test-export", format="md")
        assert "successfully" in result.lower()
        assert ".md" in result
        assert os.path.exists("data/exports/test-export.md")

    def test_export_txt(self, exporter):
        content = "## Title\n\nSome **bold** text."
        result = exporter.execute(content=content, filename="test-txt", format="txt")
        assert "successfully" in result.lower()
        assert ".txt" in result
        assert os.path.exists("data/exports/test-txt.txt")

        with open("data/exports/test-txt.txt", "r") as f:
            txt = f.read()
            assert "##" not in txt
            assert "**" not in txt

    def test_export_docx(self, exporter):
        content = "## Summary\n\n- Point 1\n- Point 2\n\n**Bold text** here."
        result = exporter.execute(content=content, filename="test-docx", format="docx")
        assert "successfully" in result.lower()
        assert ".docx" in result
        assert os.path.exists("data/exports/test-docx.docx")

    def test_export_html(self, exporter):
        content = "# Title\n\nSome **bold** content with `code`."
        result = exporter.execute(content=content, filename="test-html", format="html")
        assert "successfully" in result.lower()
        assert ".html" in result
        assert os.path.exists("data/exports/test-html.html")

        with open("data/exports/test-html.html", "r") as f:
            html = f.read()
            assert "<h1>" in html
            assert "<strong>" in html
            assert "<code>" in html

    def test_auto_filename(self, exporter):
        """When no filename given, auto-generate from first line."""
        content = "# Transformer Architecture\n\nLots of content here..."
        result = exporter.execute(content=content, format="md")
        assert "successfully" in result.lower()

    def test_default_format_is_md(self, exporter):
        """Default format should be md when not specified."""
        content = "Just some text"
        result = exporter.execute(content=content, filename="default-test")
        assert ".md" in result

    def test_unsupported_format(self, exporter):
        result = exporter.execute(content="test", filename="bad", format="xyz")
        assert "unsupported" in result.lower()

    def test_export_by_note_query(self, exporter):
        """Export a specific note by keyword search."""
        session = Session(session_id="export-test")
        session.notes = [
            Note(content="## Transformer\n\nUses self-attention mechanism.", tags=["AI", "NLP"]),
            Note(content="## Python\n\nA popular programming language.", tags=["programming"]),
            Note(content="## Database Indexing\n\nB-Tree is a common index structure.", tags=["database"]),
        ]

        result = exporter.execute(
            note_query="Transformer", format="md", session=session
        )
        assert "successfully" in result.lower()
        assert "Transformer" in result

    def test_export_by_note_query_no_match(self, exporter):
        """When no note matches, return helpful error."""
        session = Session(session_id="export-test-2")
        session.notes = [Note(content="Python stuff", tags=["programming"])]

        result = exporter.execute(note_query="quantum physics", session=session)
        assert "no note matched" in result.lower()

    def test_export_by_note_query_with_filename(self, exporter):
        """note_query + custom filename."""
        session = Session(session_id="export-test-3")
        session.notes = [Note(content="## React Hooks\n\nuseState and useEffect...", tags=["react"])]

        result = exporter.execute(
            note_query="react", filename="my-react-notes", format="docx", session=session
        )
        assert "successfully" in result.lower()
        assert ".docx" in result
        assert os.path.exists("data/exports/my-react-notes.docx")
