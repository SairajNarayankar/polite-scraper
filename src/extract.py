"""HTML extraction for catalogue pages and book detail pages."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

CATALOGUE_START = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


def parse_catalogue_page(html: str, page_url: str) -> tuple[list[str], str | None]:
    """Return absolute book URLs and the next catalogue page URL, if any."""
    soup = BeautifulSoup(html, "html.parser")
    book_urls: list[str] = []
    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a[href]")
        if not link:
            continue
        book_urls.append(urljoin(page_url, link["href"]))

    next_url = None
    next_link = soup.select_one("li.next a[href]")
    if next_link:
        next_url = urljoin(page_url, next_link["href"])
    return book_urls, next_url


def extract_raw_book(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> dict:
    """
    Pull the eight raw fields from the product area of a book page.

    Missing description is stored as None — never invented.
    """
    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("article.product_page") or soup

    title_el = product.select_one("div.product_main h1")
    price_el = product.select_one("div.product_main p.price_color")
    avail_el = product.select_one("div.product_main p.instock.availability")
    rating_el = product.select_one("div.product_main p.star-rating")

    description = None
    desc_header = product.select_one("#product_description")
    if desc_header:
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            text = desc_p.get_text(" ", strip=True)
            description = text or None

    rating_text = None
    if rating_el:
        classes = rating_el.get("class", [])
        words = [c for c in classes if c != "star-rating"]
        rating_text = words[0] if words else None

    availability_text = None
    if avail_el:
        availability_text = " ".join(avail_el.get_text(" ", strip=True).split()) or None

    return {
        "title": title_el.get_text(strip=True) if title_el else None,
        "product_url": product_url,
        "price_text": price_el.get_text(strip=True) if price_el else None,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


def normalize_price_gbp(price_text: str | None) -> float | None:
    """Turn '£51.77' (or similar) into 51.77. Returns None if unparseable."""
    if not price_text:
        return None
    match = re.search(r"(\d+(?:[.,]\d+)?)", price_text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def to_absolute_url(href: str, base_url: str) -> str:
    return urljoin(base_url, href)
