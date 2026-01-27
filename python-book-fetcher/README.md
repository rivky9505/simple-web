# Python Book Fetcher

A simple Python CLI tool that fetches books from the [OpenLibrary API](https://openlibrary.org/developers/api) using **Pydantic** for data validation and applies configurable filters.

## Features

- 📚 Fetches books from OpenLibrary Search API
- ✅ Pydantic v2 models for request/response validation
- 🔍 **2 Filter Criteria**:
  - `title_contains` - Filter books by title substring
  - `min_year` - Filter books published on or after a specific year
- 📄 JSON output with clean, structured data
- 🧪 Unit tests with pytest

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Run with defaults (search: "python", min_year: 2015, title_contains: "python")
python book_fetcher.py

# Custom search with filters
python book_fetcher.py --query "kubernetes" --title-contains "docker" --min-year 2020

# Limit results and specify output file
python book_fetcher.py --query "python programming" --max-results 10 --output my_books.json
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--query` | Search query for OpenLibrary | `python` |
| `--title-contains` | Filter: title must contain this string | `python` |
| `--min-year` | Filter: minimum publish year | `2015` |
| `--max-results` | Maximum number of filtered results | `20` |
| `--api-limit` | Number of results to fetch from API | `100` |
| `--output` | Output JSON file path | `filtered_books.json` |
| `--timeout-s` | HTTP request timeout in seconds | `15` |

## Output Format

```json
[
  {
    "title": "Python Programming",
    "author_name": ["John Doe"],
    "first_publish_year": 2020,
    "key": "/works/OL12345W"
  }
]
```

## Running Tests

```bash
pytest test_book_fetcher.py -v
```

---

## CI/CD Pipelines

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs automatically on every push and pull request:

- ✅ Sets up Python 3.11
- ✅ Installs dependencies
- ✅ Runs unit tests with pytest
- ✅ Executes the script with default parameters
- ✅ Validates output file exists and contains valid JSON
- ✅ Uploads `filtered_books.json` as an artifact

### 2. Manual Run Workflow (`.github/workflows/run-book-fetcher.yml`)

Trigger manually from GitHub Actions UI with custom parameters:

| Input | Description | Default |
|-------|-------------|---------|
| `query` | Search query | `python` |
| `title_contains` | Title filter | `python` |
| `min_year` | Minimum year | `2015` |
| `max_results` | Max results | `20` |

**To run manually:**
1. Go to **Actions** tab in GitHub
2. Select **"Run Book Fetcher"** workflow
3. Click **"Run workflow"**
4. Fill in parameters and run
5. Download results from **Artifacts**

---

## Project Structure

```
python-book-fetcher/
├── book_fetcher.py      # Main script (~150 lines)
├── test_book_fetcher.py # Unit tests (8 tests)
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## Dependencies

- `pydantic>=2.0.0` - Data validation
- `requests>=2.31.0` - HTTP client
- `pytest>=7.4.0` - Testing (dev)
