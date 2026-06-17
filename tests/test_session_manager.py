import json
import os
import tempfile
import pytest
from session.manager import SessionManager
from tools.base import Session, Note


class TestSessionManager:
    @pytest.fixture
    def data_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            sessions_dir = os.path.join(tmp, "sessions")
            os.makedirs(sessions_dir)
            yield sessions_dir

    @pytest.fixture
    def manager(self, data_dir):
        return SessionManager(data_dir=data_dir)

    def test_create_session(self, manager):
        session = manager.create("test-001")
        assert session.session_id == "test-001"
        assert session.messages == []
        assert session.notes == []

    def test_save_and_load_session(self, manager):
        session = manager.create("test-002")
        session.messages.append({"role": "user", "content": "Hello"})
        session.messages.append({"role": "assistant", "content": "Hi there!"})
        note = Note(content="Test knowledge", tags=["test"])
        session.notes.append(note)

        manager.save(session)

        loaded = manager.load("test-002")
        assert loaded.session_id == "test-002"
        assert len(loaded.messages) == 2
        assert loaded.messages[0]["content"] == "Hello"
        assert len(loaded.notes) == 1
        assert loaded.notes[0].content == "Test knowledge"

    def test_load_non_existent_session(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.load("non-existent")

    def test_list_sessions(self, manager):
        manager.save(manager.create("a"))
        manager.save(manager.create("b"))
        sessions = manager.list_sessions()
        assert "a" in sessions
        assert "b" in sessions

    def test_get_related_notes_keyword_match(self, manager):
        session = manager.create("test-003")
        session.notes = [
            Note(content="Transformer uses self-attention mechanism.", tags=["AI"]),
            Note(content="Python is a programming language.", tags=["programming"]),
            Note(content="Self-attention computes weighted sums of values.", tags=["AI", "attention"]),
        ]

        results = manager.get_related_notes(session, "attention mechanism", top_k=3)
        assert len(results) >= 1
        first_content = results[0].content.lower()
        assert "self-attention" in first_content or "attention" in first_content

    def test_get_related_notes_no_match(self, manager):
        session = manager.create("test-004")
        session.notes = [Note(content="Only about Python.", tags=["programming"])]

        results = manager.get_related_notes(session, "quantum physics", top_k=3)
        assert results == []

    def test_get_related_notes_empty_notes(self, manager):
        session = manager.create("test-005")
        results = manager.get_related_notes(session, "anything", top_k=3)
        assert results == []

    def test_save_and_load_preserves_created_at(self, manager):
        session = manager.create("test-006")
        original_created = session.created_at
        manager.save(session)

        loaded = manager.load("test-006")
        assert loaded.created_at == original_created

    def test_corrupted_session_file(self, manager, data_dir):
        """Corrupted session files should raise an error."""
        filepath = os.path.join(data_dir, "corrupt.json")
        with open(filepath, "w") as f:
            f.write("this is not valid json {{{")

        with pytest.raises(Exception):
            manager.load("corrupt")
