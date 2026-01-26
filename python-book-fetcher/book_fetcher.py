#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import List, Optional, Protocol

import requests
from pydantic import BaseModel, Field, ValidationError


# -----------------------------
# Pydantic models (API response)
# -----------------------------
class Book(BaseModel):
    title: str
    author_name: List[str] = Field(default_factory=list)
    first_publish_year: Optional[int] = None
    key: Optional[str] = None  # e.g. "/works/OL12345W"


class OpenLibrarySearchResponse(BaseModel):
    numFound: int = 0
    docs: List[Book] = Field(default_factory=list)


# -----------------------------
# Pydantic config model (defaults live here)
# -----------------------------
class FetchConfig(BaseModel):
    query: str = "python"
    title_contains: str = "python"
    min_year: int = 2015
    max_results: int = 20
    api_limit: int = 100
    output: str = "filtered_books.json"
    timeout_s: int = 15


# -----------------------------
# Output (extensible design)
# -----------------------------
class OutputWriter(Protocol):
    def write(self, books: List[Book], out_path: str) -> None:
        ...


@dataclass
class JsonWriter:
    indent: int = 2

    def write(self, books: List[Book], out_path: str) -> None:
        payload = [b.model_dump() for b in books]  # Pydantic v2
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=self.indent)


# -----------------------------
# Fetching
# -----------------------------
def fetch_books(cfg: FetchConfig) -> OpenLibrarySearchResponse:
    url = "https://openlibrary.org/search.json"
    resp = requests.get(
        url,
        params={"q": cfg.query, "limit": cfg.api_limit},
        timeout=cfg.timeout_s,
    )
    resp.raise_for_status()
    return OpenLibrarySearchResponse.model_validate(resp.json())  # Pydantic v2


# -----------------------------
# Filtering (2 criteria)
# - title contains substring
# - first_publish_year >= min_year
# -----------------------------
def filter_books(cfg: FetchConfig, books: List[Book]) -> List[Book]:
    needle = cfg.title_contains.strip().lower()

    filtered: List[Book] = []
    for b in books:
        if needle and needle not in b.title.lower():
            continue
        if b.first_publish_year is None or b.first_publish_year < cfg.min_year:
            continue

        filtered.append(b)
        if len(filtered) >= cfg.max_results:
            break

    return filtered


# -----------------------------
# CLI -> Config
# Only overrides values that user actually provided.
# -----------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Small Book Fetcher (OpenLibrary + Pydantic)")

    # All optional: if not provided => None, so config defaults remain.
    p.add_argument("--query", default=None, help="Search query (default from config)")
    p.add_argument("--title-contains", dest="title_contains", default=None, help="Filter title contains (default from config)")
    p.add_argument("--min-year", dest="min_year", type=int, default=None, help="Filter min publish year (default from config)")
    p.add_argument("--max-results", dest="max_results", type=int, default=None, help="Max filtered results (default from config)")
    p.add_argument("--api-limit", dest="api_limit", type=int, default=None, help="API limit (default from config)")
    p.add_argument("--output", default=None, help="Output JSON file path (default from config)")
    p.add_argument("--timeout-s", dest="timeout_s", type=int, default=None, help="HTTP timeout seconds (default from config)")

    return p.parse_args()


def build_config(args: argparse.Namespace) -> FetchConfig:
    overrides = {k: v for k, v in vars(args).items() if v is not None}
    # Pydantic will apply defaults for anything missing
    return FetchConfig.model_validate(overrides)


# -----------------------------
# main
# -----------------------------
def main() -> int:
    try:
        args = parse_args()
        cfg = build_config(args)

        response = fetch_books(cfg)
        filtered = filter_books(cfg, response.docs)

        writer: OutputWriter = JsonWriter()
        writer.write(filtered, cfg.output)

        print(f"Wrote {len(filtered)} books to {cfg.output}")
        return 0

    except requests.RequestException as e:
        print(f"HTTP error: {e}")
        return 2
    except ValidationError as e:
        print(f"Validation error: {e}")
        return 3
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
