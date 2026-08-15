"""
FlyRank Internship · Backend Track · Week 5 · Assignment A9
The polite scraper — Books to Scrape, first 3 catalogue pages, 60 books.
"""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import requests

from extract import (
    CATALOGUE_START,
    MAX_CATALOGUE_PAGES,
    extract_raw_book,
    normalize_price_gbp,
    parse_catalogue_page,
)
from fetch import fetch_page, polite_pause
from schema import validate_record

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
FAKE_FAILURE_URL = "https://books.toscrape.com/catalogue/this-book-does-not-exist-a9/index.html"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_books(session: requests.Session, stats: dict) -> tuple[list[str], dict[str, str]]:
    """Walk the catalogue's own 'next' link for three pages. Do not hardcode book URLs."""
    page_url = CATALOGUE_START
    discovered: list[str] = []
    source_of: dict[str, str] = {}
    pages = 0

    while page_url and pages < MAX_CATALOGUE_PAGES:
        result = fetch_page(page_url, session=session, stats=stats)
        polite_pause(result.from_cache)
        if result.html is None:
            print(f"FAILED     catalogue page {page_url} error={result.error}")
            stats.setdefault("failed_pages", []).append(
                {"url": page_url, "error": result.error, "kind": "catalogue"}
            )
            break

        book_urls, next_url = parse_catalogue_page(result.html, page_url)
        for url in book_urls:
            discovered.append(url)
            source_of.setdefault(url, page_url)
        pages += 1
        print(
            f"CATALOGUE  page={pages} url={page_url} books_on_page={len(book_urls)} "
            f"next={'yes' if next_url else 'no'}"
        )
        page_url = next_url

    unique = list(dict.fromkeys(discovered))
    print(
        f"catalogue_pages={pages} discovered={len(discovered)} unique_urls={len(unique)}"
    )
    return unique, source_of


def scrape_book(
    url: str,
    source_page: str,
    session: requests.Session,
    stats: dict,
) -> tuple[dict | None, dict | None, dict | None]:
    """
    Fetch one book page and return (valid_record, invalid_error, failed_page).
    One broken page never kills the run.
    """
    result = fetch_page(url, session=session, stats=stats)
    polite_pause(result.from_cache)
    if result.html is None:
        failed = {
            "url": url,
            "error": result.error,
            "status_code": result.status_code,
            "attempts": result.attempts,
            "kind": "detail",
        }
        print(f"SKIP       url={url} error={result.error}")
        return None, None, failed

    raw = extract_raw_book(result.html, url, source_page, result.fetched_at)
    candidate = {
        **raw,
        "price_gbp": normalize_price_gbp(raw.get("price_text")),
    }
    record, reason = validate_record(candidate)
    if record is None:
        invalid = {"record": candidate, "reason": reason, "url": url}
        print(f"INVALID    url={url} reason={reason}")
        return None, invalid, None
    return record.model_dump(), None, None


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_sample_raw(html: str, url: str, source_page: str, fetched_at: str) -> None:
    raw = extract_raw_book(html, url, source_page, fetched_at)
    print("RAW RECORD SAMPLE")
    print(json.dumps(raw, indent=2, ensure_ascii=False))
    print(f"raw_keys={sorted(raw.keys())} key_count={len(raw)}")


def run() -> int:
    started = datetime.now(timezone.utc)
    stats = {
        "pages_fetched": 0,
        "cache_hits": 0,
        "failed_pages": [],
    }
    session = requests.Session()

    unique_urls, source_of = discover_books(session, stats)

    # Stage 5 proof: one made-up URL on our side. Never hammer the real site to test failure.
    book_urls = unique_urls + [FAKE_FAILURE_URL]
    source_of[FAKE_FAILURE_URL] = CATALOGUE_START

    valid_by_url: OrderedDict[str, dict] = OrderedDict()
    invalid: list[dict] = []
    sample_printed = False

    for url in book_urls:
        record, bad, failed = scrape_book(url, source_of.get(url, CATALOGUE_START), session, stats)
        if failed:
            stats["failed_pages"].append(failed)
            continue
        if bad:
            invalid.append(bad)
            continue
        if record is None:
            continue
        # Canonical identity is the absolute product URL — reruns update, never duplicate.
        valid_by_url[record["product_url"]] = record
        if not sample_printed:
            print("RAW RECORD SAMPLE")
            raw_keys = {
                "title": record["title"],
                "product_url": record["product_url"],
                "price_text": record["price_text"],
                "availability_text": record["availability_text"],
                "rating_text": record["rating_text"],
                "description": record["description"],
                "source_page": record["source_page"],
                "fetched_at": record["fetched_at"],
            }
            print(json.dumps(raw_keys, indent=2, ensure_ascii=False))
            sample_printed = True

    books = list(valid_by_url.values())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "books.json", books)
    write_json(OUTPUT_DIR / "errors.json", invalid)

    ended = datetime.now(timezone.utc)
    report = {
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round((ended - started).total_seconds(), 2),
        "catalogue_pages": MAX_CATALOGUE_PAGES,
        "discovered": len(unique_urls),
        "unique_urls": len(unique_urls),
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": len(books),
        "invalid_records": len(invalid),
        "failed_pages": len(stats["failed_pages"]),
        "failed_page_details": stats["failed_pages"],
    }
    write_json(OUTPUT_DIR / "run-report.json", report)

    print(f"detail_pages={len(unique_urls)}")
    print(
        f"REPORT     valid={report['valid_records']} invalid={report['invalid_records']} "
        f"failed_pages={report['failed_pages']} fetched={report['pages_fetched']} "
        f"cache_hits={report['cache_hits']} duration_s={report['duration_seconds']}"
    )
    return 0 if report["valid_records"] == 60 and report["failed_pages"] == 1 else 1


if __name__ == "__main__":
    sys.exit(run())
