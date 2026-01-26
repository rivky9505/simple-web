"""Tests for the Book Fetcher application."""

import pytest
from unittest.mock import patch, Mock

from book_fetcher import (
    Book,
    FetchConfig,
    OpenLibrarySearchResponse,
    JsonWriter,
    fetch_books,
    filter_books,
)


# ============================================================================
# Model Tests
# ============================================================================

class TestBookModel:
    def test_book_creation(self):
        book = Book(title="Test Book", author_name=["Author"], first_publish_year=2020)
        assert book.title == "Test Book"
        assert book.author_name == ["Author"]
        assert book.first_publish_year == 2020

    def test_book_defaults(self):
        book = Book(title="Minimal Book")
        assert book.author_name == []
        assert book.first_publish_year is None


class TestFetchConfig:
    def test_defaults(self):
        cfg = FetchConfig()
        assert cfg.query == "python"
        assert cfg.title_contains == "python"
        assert cfg.min_year == 2015
        assert cfg.max_results == 20

    def test_override(self):
        cfg = FetchConfig(query="javascript", min_year=2020)
        assert cfg.query == "javascript"
        assert cfg.min_year == 2020


# ============================================================================
# Filter Tests
# ============================================================================

class TestFilterBooks:
    @pytest.fixture
    def sample_books(self):
        return [
            Book(title="Learning Python", author_name=["Mark Lutz"], first_publish_year=2016),
            Book(title="Python Crash Course", author_name=["Eric Matthes"], first_publish_year=2019),
            Book(title="JavaScript Guide", author_name=["David"], first_publish_year=2018),
            Book(title="Old Python Book", author_name=["Someone"], first_publish_year=2010),
        ]

    def test_filter_by_title_and_year(self, sample_books):
        cfg = FetchConfig(title_contains="python", min_year=2015)
        filtered = filter_books(cfg, sample_books)
        
        assert len(filtered) == 2
        assert all("python" in b.title.lower() for b in filtered)
        assert all(b.first_publish_year >= 2015 for b in filtered)

    def test_filter_respects_max_results(self, sample_books):
        cfg = FetchConfig(title_contains="", min_year=2000, max_results=2)
        filtered = filter_books(cfg, sample_books)
        
        assert len(filtered) == 2


# ============================================================================
# Output Tests
# ============================================================================

class TestJsonWriter:
    def test_writes_json(self, tmp_path):
        books = [Book(title="Test", author_name=["Auth"], first_publish_year=2020)]
        writer = JsonWriter()
        out_path = tmp_path / "out.json"
        
        writer.write(books, str(out_path))
        
        import json
        data = json.loads(out_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test"


# ============================================================================
# API Client Tests
# ============================================================================

class TestFetchBooks:
    @patch('book_fetcher.requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "numFound": 1,
            "docs": [{"title": "Python Book", "author_name": ["Author"], "first_publish_year": 2020}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        cfg = FetchConfig()
        result = fetch_books(cfg)
        
        assert isinstance(result, OpenLibrarySearchResponse)
        assert len(result.docs) == 1
        assert result.docs[0].title == "Python Book"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
