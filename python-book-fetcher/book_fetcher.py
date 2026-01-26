"""
Book Fetcher Module
===================
A robust Python application that fetches book data from the Open Library API,
validates it using Pydantic models, and exports filtered results in multiple formats.

This module demonstrates:
- API integration with error handling and retries
- Data validation using Pydantic v2
- Extensible output format architecture (Strategy Pattern)
- Type hints and documentation
- Professional code structure
"""

from typing import List, Optional, Protocol
from datetime import datetime
from pathlib import Path
import json
import logging
from abc import ABC, abstractmethod

import requests
from pydantic import BaseModel, Field, field_validator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Data Validation
# ============================================================================

class BookAuthor(BaseModel):
    """Represents a book author with validation."""
    name: str = Field(..., description="Author's full name", min_length=1)
    
    @field_validator('name')
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Clean and normalize author name."""
        return v.strip()


class Book(BaseModel):
    """
    Represents a book with comprehensive metadata.
    
    This model validates and structures book data from the Open Library API.
    Only essential fields are required, making it flexible for various API responses.
    """
    title: str = Field(..., description="Book title", min_length=1)
    authors: List[str] = Field(default_factory=list, description="List of author names")
    first_publish_year: Optional[int] = Field(None, description="Year of first publication", ge=1000, le=2100)
    isbn: Optional[List[str]] = Field(default_factory=list, description="List of ISBN numbers")
    publisher: Optional[List[str]] = Field(default_factory=list, description="List of publishers")
    language: Optional[List[str]] = Field(default_factory=list, description="Languages the book is available in")
    number_of_pages: Optional[int] = Field(None, description="Number of pages", ge=1)
    subjects: Optional[List[str]] = Field(default_factory=list, description="Book subjects/categories")
    
    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.now, description="When this data was fetched")
    
    @field_validator('title')
    @classmethod
    def clean_title(cls, v: str) -> str:
        """Clean and normalize book title."""
        return v.strip()
    
    @field_validator('authors', mode='before')
    @classmethod
    def extract_authors(cls, v):
        """Extract author names from various formats."""
        if not v:
            return []
        if isinstance(v, list):
            # Handle list of strings or list of dicts
            authors = []
            for author in v:
                if isinstance(author, str):
                    authors.append(author)
                elif isinstance(author, dict) and 'name' in author:
                    authors.append(author['name'])
            return authors
        return []
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Learning Python",
                "authors": ["Mark Lutz"],
                "first_publish_year": 1999,
                "isbn": ["9780596158064"],
                "publisher": ["O'Reilly Media"],
                "language": ["eng"],
                "number_of_pages": 1594
            }
        }
    }


class APIResponse(BaseModel):
    """Validates the top-level API response structure."""
    numFound: int = Field(..., description="Total number of results found")
    docs: List[dict] = Field(..., description="List of book documents")
    start: int = Field(0, description="Starting offset for pagination")


# ============================================================================
# Output Format Abstraction (Strategy Pattern)
# ============================================================================

class OutputFormatter(Protocol):
    """
    Protocol defining the interface for output formatters.
    This makes it easy to add new output formats (CSV, XML, YAML, etc.)
    """
    
    def format(self, books: List[Book], output_path: Path) -> None:
        """Format and write books to the specified output path."""
        ...


class JSONFormatter:
    """Formats book data as JSON."""
    
    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        self.indent = indent
        self.ensure_ascii = ensure_ascii
    
    def format(self, books: List[Book], output_path: Path) -> None:
        """Write books to JSON file with proper formatting."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert Pydantic models to dictionaries
        books_data = [book.model_dump(mode='json') for book in books]
        
        # Add metadata
        output = {
            "metadata": {
                "total_books": len(books),
                "generated_at": datetime.now().isoformat(),
                "format_version": "1.0"
            },
            "books": books_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=self.indent, ensure_ascii=self.ensure_ascii)
        
        logger.info(f"Successfully wrote {len(books)} books to {output_path}")


# Future formatters can be easily added:
# class CSVFormatter:
#     def format(self, books: List[Book], output_path: Path) -> None:
#         ...
#
# class YAMLFormatter:
#     def format(self, books: List[Book], output_path: Path) -> None:
#         ...


# ============================================================================
# Book Filter Classes
# ============================================================================

class BookFilter(ABC):
    """Abstract base class for book filters."""
    
    @abstractmethod
    def matches(self, book: Book) -> bool:
        """Return True if the book matches the filter criteria."""
        pass


class TitleContainsFilter(BookFilter):
    """Filter books whose title contains a specific keyword."""
    
    def __init__(self, keyword: str, case_sensitive: bool = False):
        self.keyword = keyword
        self.case_sensitive = case_sensitive
    
    def matches(self, book: Book) -> bool:
        title = book.title if self.case_sensitive else book.title.lower()
        keyword = self.keyword if self.case_sensitive else self.keyword.lower()
        return keyword in title


class YearRangeFilter(BookFilter):
    """Filter books published within a specific year range."""
    
    def __init__(self, min_year: Optional[int] = None, max_year: Optional[int] = None):
        self.min_year = min_year
        self.max_year = max_year
    
    def matches(self, book: Book) -> bool:
        if book.first_publish_year is None:
            return False
        
        if self.min_year and book.first_publish_year < self.min_year:
            return False
        
        if self.max_year and book.first_publish_year > self.max_year:
            return False
        
        return True


class AuthorFilter(BookFilter):
    """Filter books by author name."""
    
    def __init__(self, author_name: str, case_sensitive: bool = False):
        self.author_name = author_name
        self.case_sensitive = case_sensitive
    
    def matches(self, book: Book) -> bool:
        if not book.authors:
            return False
        
        for author in book.authors:
            author_check = author if self.case_sensitive else author.lower()
            name_check = self.author_name if self.case_sensitive else self.author_name.lower()
            if name_check in author_check:
                return True
        return False


# ============================================================================
# API Client
# ============================================================================

class OpenLibraryClient:
    """
    Client for interacting with the Open Library API.
    
    Includes retry logic, timeout handling, and proper error handling.
    """
    
    BASE_URL = "https://openlibrary.org"
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.session = self._create_session(max_retries)
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def search_books(
        self, 
        query: str, 
        limit: int = 100,
        fields: Optional[List[str]] = None
    ) -> List[Book]:
        """
        Search for books using the Open Library API.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            fields: Specific fields to request (None = all fields)
        
        Returns:
            List of Book objects
        
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}/search.json"
        
        params = {
            "q": query,
            "limit": limit
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        logger.info(f"Searching Open Library for: {query}")
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Validate response structure
            api_response = APIResponse.model_validate(response.json())
            
            logger.info(f"Found {api_response.numFound} results, processing {len(api_response.docs)} books")
            
            # Parse books with error handling
            books = []
            for doc in api_response.docs:
                try:
                    book = self._parse_book(doc)
                    if book:
                        books.append(book)
                except Exception as e:
                    logger.warning(f"Failed to parse book: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(books)} books")
            return books
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def _parse_book(self, doc: dict) -> Optional[Book]:
        """Parse a book document from the API response."""
        try:
            # Map API fields to our Book model
            book_data = {
                "title": doc.get("title", ""),
                "authors": doc.get("author_name", []),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", []),
                "publisher": doc.get("publisher", []),
                "language": doc.get("language", []),
                "number_of_pages": doc.get("number_of_pages_median"),
                "subjects": doc.get("subject", [])[:10]  # Limit subjects to avoid too much data
            }
            
            return Book(**book_data)
        except Exception as e:
            logger.debug(f"Error parsing book document: {e}")
            return None


# ============================================================================
# Main Book Fetcher Class
# ============================================================================

class BookFetcher:
    """
    Main class that orchestrates fetching, filtering, and exporting books.
    
    This class demonstrates the Single Responsibility Principle and
    Dependency Injection patterns.
    """
    
    def __init__(
        self,
        client: Optional[OpenLibraryClient] = None,
        formatter: Optional[OutputFormatter] = None
    ):
        self.client = client or OpenLibraryClient()
        self.formatter = formatter or JSONFormatter()
    
    def fetch_and_filter(
        self,
        query: str,
        filters: List[BookFilter],
        limit: int = 100
    ) -> List[Book]:
        """
        Fetch books from the API and apply filters.
        
        Args:
            query: Search query
            filters: List of BookFilter objects to apply
            limit: Maximum number of books to fetch
        
        Returns:
            Filtered list of Book objects
        """
        # Fetch books from API
        books = self.client.search_books(query, limit=limit)
        
        logger.info(f"Applying {len(filters)} filters to {len(books)} books")
        
        # Apply all filters
        filtered_books = books
        for book_filter in filters:
            filtered_books = [
                book for book in filtered_books 
                if book_filter.matches(book)
            ]
            logger.info(f"After {book_filter.__class__.__name__}: {len(filtered_books)} books remaining")
        
        return filtered_books
    
    def export(self, books: List[Book], output_path: Path) -> None:
        """Export books using the configured formatter."""
        self.formatter.format(books, output_path)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Main function demonstrating the book fetcher functionality.
    
    This example searches for Python books and applies two filters:
    1. Title must contain "python"
    2. Published between 2010 and 2024
    """
    
    # Initialize the book fetcher
    fetcher = BookFetcher(
        client=OpenLibraryClient(timeout=15),
        formatter=JSONFormatter(indent=2)
    )
    
    # Define search query
    search_query = "python programming"
    
    # Define filters (you can easily modify these)
    filters = [
        TitleContainsFilter("python", case_sensitive=False),
        YearRangeFilter(min_year=2010, max_year=2024)
    ]
    
    logger.info("=" * 80)
    logger.info("Book Fetcher - Starting")
    logger.info("=" * 80)
    logger.info(f"Search Query: {search_query}")
    logger.info(f"Filters: {[f.__class__.__name__ for f in filters]}")
    
    try:
        # Fetch and filter books
        books = fetcher.fetch_and_filter(
            query=search_query,
            filters=filters,
            limit=100
        )
        
        logger.info(f"Final result: {len(books)} books match all criteria")
        
        # Export to JSON
        output_path = Path("output/filtered_books.json")
        fetcher.export(books, output_path)
        
        logger.info("=" * 80)
        logger.info(f"✓ Successfully exported {len(books)} books to {output_path}")
        logger.info("=" * 80)
        
        # Print some statistics
        if books:
            print("\n📚 Sample Books Found:")
            for book in books[:5]:  # Show first 5 books
                print(f"  • {book.title} ({book.first_publish_year}) by {', '.join(book.authors[:2])}")
        
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
