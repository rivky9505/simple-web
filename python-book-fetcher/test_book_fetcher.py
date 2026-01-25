"""
Test suite for the Book Fetcher application.

This demonstrates testing best practices including:
- Unit tests for individual components
- Integration tests for API interactions
- Mocking external dependencies
- Parameterized tests
"""

import pytest
from datetime import datetime
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock

from book_fetcher import (
    Book,
    BookFetcher,
    OpenLibraryClient,
    TitleContainsFilter,
    YearRangeFilter,
    AuthorFilter,
    JSONFormatter
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_books():
    """Fixture providing sample book data for testing."""
    return [
        Book(
            title="Learning Python",
            authors=["Mark Lutz"],
            first_publish_year=2013,
            isbn=["9781449355739"],
            publisher=["O'Reilly Media"]
        ),
        Book(
            title="Python Crash Course",
            authors=["Eric Matthes"],
            first_publish_year=2019,
            isbn=["9781593279288"]
        ),
        Book(
            title="Fluent Python",
            authors=["Luciano Ramalho"],
            first_publish_year=2015,
            isbn=["9781491946008"]
        ),
        Book(
            title="JavaScript: The Good Parts",
            authors=["Douglas Crockford"],
            first_publish_year=2008,
            isbn=["9780596517748"]
        )
    ]


@pytest.fixture
def mock_api_response():
    """Fixture providing mock API response data."""
    return {
        "numFound": 2,
        "start": 0,
        "docs": [
            {
                "title": "Learning Python",
                "author_name": ["Mark Lutz"],
                "first_publish_year": 2013,
                "isbn": ["9781449355739"]
            },
            {
                "title": "Python Crash Course",
                "author_name": ["Eric Matthes"],
                "first_publish_year": 2019
            }
        ]
    }


# ============================================================================
# Model Tests
# ============================================================================

class TestBookModel:
    """Tests for the Book Pydantic model."""
    
    def test_book_creation_with_all_fields(self):
        """Test creating a book with all fields."""
        book = Book(
            title="Test Book",
            authors=["Test Author"],
            first_publish_year=2020,
            isbn=["1234567890"],
            publisher=["Test Publisher"],
            language=["eng"],
            number_of_pages=300
        )
        
        assert book.title == "Test Book"
        assert book.authors == ["Test Author"]
        assert book.first_publish_year == 2020
        assert isinstance(book.fetched_at, datetime)
    
    def test_book_creation_with_minimal_fields(self):
        """Test creating a book with only required fields."""
        book = Book(title="Minimal Book")
        
        assert book.title == "Minimal Book"
        assert book.authors == []
        assert book.first_publish_year is None
    
    def test_book_title_whitespace_cleaning(self):
        """Test that book titles are cleaned of extra whitespace."""
        book = Book(title="  Test Book  ")
        assert book.title == "Test Book"
    
    def test_invalid_year(self):
        """Test that invalid years raise validation errors."""
        with pytest.raises(ValueError):
            Book(title="Test", first_publish_year=999)  # Too early
        
        with pytest.raises(ValueError):
            Book(title="Test", first_publish_year=2101)  # Too late


# ============================================================================
# Filter Tests
# ============================================================================

class TestFilters:
    """Tests for book filter classes."""
    
    def test_title_contains_filter_case_insensitive(self, sample_books):
        """Test title filter with case-insensitive matching."""
        filter_obj = TitleContainsFilter("python", case_sensitive=False)
        
        filtered = [book for book in sample_books if filter_obj.matches(book)]
        
        assert len(filtered) == 3
        assert all("python" in book.title.lower() for book in filtered)
    
    def test_title_contains_filter_case_sensitive(self, sample_books):
        """Test title filter with case-sensitive matching."""
        filter_obj = TitleContainsFilter("Python", case_sensitive=True)
        
        filtered = [book for book in sample_books if filter_obj.matches(book)]
        
        assert len(filtered) == 3
    
    def test_year_range_filter_min_year(self, sample_books):
        """Test year range filter with minimum year."""
        filter_obj = YearRangeFilter(min_year=2015)
        
        filtered = [book for book in sample_books if filter_obj.matches(book)]
        
        assert len(filtered) == 2
        assert all(book.first_publish_year >= 2015 for book in filtered if book.first_publish_year)
    
    def test_year_range_filter_max_year(self, sample_books):
        """Test year range filter with maximum year."""
        filter_obj = YearRangeFilter(max_year=2015)
        
        filtered = [book for book in sample_books if filter_obj.matches(book)]
        
        assert len(filtered) == 3
    
    def test_year_range_filter_range(self, sample_books):
        """Test year range filter with both min and max."""
        filter_obj = YearRangeFilter(min_year=2010, max_year=2018)
        
        filtered = [book for book in sample_books if filter_obj.matches(book)]
        
        assert len(filtered) == 2
    
    def test_author_filter(self, sample_books):
        """Test author filter."""
        filter_obj = AuthorFilter("Lutz", case_sensitive=False)
        
        filtered = [book for book in sample_books if filter_obj.matches(book)]
        
        assert len(filtered) == 1
        assert filtered[0].title == "Learning Python"


# ============================================================================
# Formatter Tests
# ============================================================================

class TestJSONFormatter:
    """Tests for JSON output formatter."""
    
    def test_json_formatter_creates_valid_json(self, sample_books, tmp_path):
        """Test that JSON formatter creates valid JSON output."""
        formatter = JSONFormatter()
        output_path = tmp_path / "test_output.json"
        
        formatter.format(sample_books[:2], output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "books" in data
        assert data["metadata"]["total_books"] == 2
        assert len(data["books"]) == 2
    
    def test_json_formatter_creates_directory(self, sample_books, tmp_path):
        """Test that JSON formatter creates parent directories."""
        formatter = JSONFormatter()
        output_path = tmp_path / "subdir" / "output.json"
        
        formatter.format(sample_books, output_path)
        
        assert output_path.exists()


# ============================================================================
# API Client Tests
# ============================================================================

class TestOpenLibraryClient:
    """Tests for the Open Library API client."""
    
    @patch('book_fetcher.requests.Session.get')
    def test_search_books_success(self, mock_get, mock_api_response):
        """Test successful book search."""
        mock_response = Mock()
        mock_response.json.return_value = mock_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = OpenLibraryClient()
        books = client.search_books("python")
        
        assert len(books) == 2
        assert all(isinstance(book, Book) for book in books)
        assert books[0].title == "Learning Python"
    
    @patch('book_fetcher.requests.Session.get')
    def test_search_books_handles_invalid_data(self, mock_get):
        """Test that client handles invalid book data gracefully."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "numFound": 2,
            "start": 0,
            "docs": [
                {"title": "Valid Book", "author_name": ["Author"]},
                {"invalid": "data"},  # This should be skipped
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = OpenLibraryClient()
        books = client.search_books("test")
        
        assert len(books) == 1  # Only the valid book


# ============================================================================
# Integration Tests
# ============================================================================

class TestBookFetcher:
    """Integration tests for the BookFetcher class."""
    
    def test_fetch_and_filter(self, sample_books):
        """Test the complete fetch and filter workflow."""
        # Mock the client
        mock_client = Mock(spec=OpenLibraryClient)
        mock_client.search_books.return_value = sample_books
        
        fetcher = BookFetcher(client=mock_client)
        
        filters = [
            TitleContainsFilter("python", case_sensitive=False),
            YearRangeFilter(min_year=2015)
        ]
        
        result = fetcher.fetch_and_filter("python", filters)
        
        assert len(result) == 2
        assert all("python" in book.title.lower() for book in result)
        assert all(book.first_publish_year >= 2015 for book in result if book.first_publish_year)
    
    def test_export(self, sample_books, tmp_path):
        """Test the export functionality."""
        mock_client = Mock(spec=OpenLibraryClient)
        fetcher = BookFetcher(client=mock_client, formatter=JSONFormatter())
        
        output_path = tmp_path / "export_test.json"
        fetcher.export(sample_books[:2], output_path)
        
        assert output_path.exists()


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
