import pytest
from tools.notes import SaveNote, SearchNotes
from tools.base import Session, Note


class TestSaveNote:
    @pytest.fixture
    def session(self):
        return Session(session_id="test-001")

    @pytest.fixture
    def save_note(self):
        return SaveNote()

    def test_save_note_adds_to_session(self, save_note, session):
        result = save_note.execute(
            content="Transformer uses self-attention mechanism.",
            tags=["AI", "NLP"],
            session=session,
        )
        assert len(session.notes) == 1
        assert session.notes[0].content == "Transformer uses self-attention mechanism."
        assert session.notes[0].tags == ["AI", "NLP"]
        assert "saved" in result.lower()
        assert session.notes[0].id in result

    def test_save_note_without_tags(self, save_note, session):
        result = save_note.execute(
            content="Python is a programming language.",
            session=session,
        )
        assert len(session.notes) == 1
        assert session.notes[0].tags == []

    def test_save_note_with_source_url(self, save_note, session):
        result = save_note.execute(
            content="Attention paper details.",
            tags=["paper"],
            source_url="https://arxiv.org/abs/1706.03762",
            session=session,
        )
        assert session.notes[0].source_url == "https://arxiv.org/abs/1706.03762"

    def test_save_note_without_session(self, save_note):
        """save_note requires a session to store the note."""
        result = save_note.execute(content="Some content")
        assert "error" in result.lower() or "no session" in result.lower()


class TestSearchNotes:
    @pytest.fixture
    def session(self):
        s = Session(session_id="test-002")
        s.notes = [
            Note(content="Transformer uses self-attention for sequence processing.", tags=["AI", "NLP"]),
            Note(content="Python is widely used in data science and web development.", tags=["programming"]),
            Note(content="Self-attention computes weighted sums of input representations.", tags=["AI", "attention"]),
        ]
        return s

    @pytest.fixture
    def search_notes(self):
        return SearchNotes()

    def test_search_notes_finds_relevant(self, search_notes, session):
        result = search_notes.execute(query="attention mechanism", session=session)
        assert "self-attention" in result.lower()
        assert "Transformer" in result

    def test_search_notes_no_match(self, search_notes, session):
        result = search_notes.execute(query="quantum computing", session=session)
        assert "no" in result.lower() or "not found" in result.lower() or "0" in result.lower()

    def test_search_notes_without_session(self, search_notes):
        result = search_notes.execute(query="attention")
        assert "error" in result.lower() or "no session" in result.lower()
