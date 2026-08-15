"""Parser tests — no live network."""

from pathlib import Path

import pytest

from extract import extract_raw_book, normalize_price_gbp, parse_catalogue_page, to_absolute_url
from schema import BookRecord, validate_record

FIXTURES = Path(__file__).parent / "fixtures"
CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
BOOK_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
FETCHED_AT = "2026-08-16T00:00:00Z"


def test_price_normalization_strips_currency():
    assert normalize_price_gbp("£51.77") == 51.77
    assert normalize_price_gbp("£  12.00") == 12.0
    assert normalize_price_gbp("no price here") is None
    assert normalize_price_gbp(None) is None


def test_relative_to_absolute_url():
    href = "a-light-in-the-attic_1000/index.html"
    assert to_absolute_url(href, CATALOGUE_URL) == BOOK_URL
    # Next-page links are also relative — join, never glue strings.
    assert (
        to_absolute_url("page-2.html", CATALOGUE_URL)
        == "https://books.toscrape.com/catalogue/page-2.html"
    )


def test_missing_description_is_null_not_invented():
    html = (FIXTURES / "book-missing-description.html").read_text(encoding="utf-8")
    raw = extract_raw_book(html, BOOK_URL, CATALOGUE_URL, FETCHED_AT)
    assert raw["description"] is None
    assert raw["title"] == "Mystery Title"
    assert set(raw.keys()) == {
        "title",
        "product_url",
        "price_text",
        "availability_text",
        "rating_text",
        "description",
        "source_page",
        "fetched_at",
    }


def test_extra_whitespace_is_normalized_in_availability():
    html = (FIXTURES / "book-missing-description.html").read_text(encoding="utf-8")
    raw = extract_raw_book(html, BOOK_URL, CATALOGUE_URL, FETCHED_AT)
    assert raw["availability_text"] == "In stock (3 available)"


def test_duplicate_urls_collapse_with_dict_fromkeys():
    html = (FIXTURES / "catalogue-page.html").read_text(encoding="utf-8")
    urls, next_url = parse_catalogue_page(html, CATALOGUE_URL)
    unique = list(dict.fromkeys(urls))
    assert len(urls) == 3
    assert len(unique) == 2
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"
    assert unique[0] == BOOK_URL


def test_malformed_fixture_fails_schema():
    html = "<html><body><p>not a book</p></body></html>"
    raw = extract_raw_book(html, "not-a-url", CATALOGUE_URL, FETCHED_AT)
    candidate = {**raw, "price_gbp": normalize_price_gbp(raw["price_text"])}
    record, reason = validate_record(candidate)
    assert record is None
    assert reason is not None


def test_valid_fixture_passes_schema():
    html = (FIXTURES / "book-with-description.html").read_text(encoding="utf-8")
    raw = extract_raw_book(html, BOOK_URL, CATALOGUE_URL, FETCHED_AT)
    candidate = {**raw, "price_gbp": normalize_price_gbp(raw["price_text"])}
    record, reason = validate_record(candidate)
    assert reason is None
    assert isinstance(record, BookRecord)
    assert record.price_gbp == 51.77
    assert record.description.startswith("It's hard to imagine")
