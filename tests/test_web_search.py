import pytest
from tools.web_search import WebSearch


class TestWebSearch:
    @pytest.fixture
    def search(self):
        return WebSearch()

    def test_search_returns_results(self, search):
        result = search.execute(query="Python programming")
        assert "Python" in result
        assert len(result) > 0

    def test_search_returns_different_results_for_different_queries(self, search):
        r1 = search.execute(query="machine learning")
        r2 = search.execute(query="web development")
        assert r1 != r2

    def test_search_no_results(self, search):
        """Searching for something very specific returns a no-results message."""
        result = search.execute(query="xyznonexistent12345")
        assert "no result" in result.lower() or "not found" in result.lower() or "0 result" in result.lower()

    def test_search_result_format(self, search):
        result = search.execute(query="Transformer architecture")
        lines = [l for l in result.split("\n") if l.strip()]
        assert len(lines) >= 1
