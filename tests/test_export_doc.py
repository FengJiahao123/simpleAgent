import os
import pytest
from tools.export_doc import ExportDoc, EXPORTERS


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

        # Verify markdown stripped
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
        assert "Transformer-Architecture" in result or "transformer" in result.lower()

    def test_default_format_is_md(self, exporter):
        """Default format should be md when not specified."""
        content = "Just some text"
        result = exporter.execute(content=content, filename="default-test")
        assert ".md" in result

    def test_unsupported_format(self, exporter):
        result = exporter.execute(content="test", filename="bad", format="xyz")
        assert "unsupported" in result.lower()
