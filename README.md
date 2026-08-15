# The polite scraper

FlyRank Internship · Backend Track · Week 5 · Assignment A9.

A small, polite scraping pipeline: download the first three catalogue pages of [Books to Scrape](https://books.toscrape.com/), visit all 60 book pages, turn messy HTML into schema-checked JSON, skip a broken page without crashing, and write an honest run report.

## Target classification

| Question | Answer |
| --- | --- |
| Which site? | [Books to Scrape](https://books.toscrape.com/), listed on [toscrape.com](https://toscrape.com/) |
| Why this site? | ToScrape describes it as a fictional bookstore that *desperately wants to be scraped* — a public practice sandbox for beginners and for validating scrapers. That sentence is the permission. |
| How much? | The first **3 catalogue pages only** (20 books each → 60 detail pages). The crawler follows the site's own "next" link and then stops. |
| What data? | Per book: title, product URL, price (raw text + `price_gbp`), availability, star rating, description (or `null`), plus provenance (`source_page`, `fetched_at`). |
| Why is that appropriate? | The site exists so people can practise this exact skill; the scope is tiny, the data is fictional, and nothing personal or gated is collected. |

**robots.txt check (2026-08-16):** `GET https://books.toscrape.com/robots.txt` returned **HTTP 404**. Result written down as: **no robots file found**. A missing file is not permission — it is just a missing file. Permission here comes from the sandbox's own statement on toscrape.com, not from a robots file.

I will not reuse this code on another site without checking its rules and terms first.

## Lane

Python 3.10+ · Requests · Beautiful Soup · Pydantic.

## Run in under 5 minutes

```bash
git clone https://github.com/SairajNarayankar/polite-scraper.git
cd polite-scraper
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

That one command writes:

- `output/books.json` — 60 validated unique records
- `output/errors.json` — schema failures (empty on a clean run)
- `output/run-report.json` — counts, cache hits, failures, duration

A second run should print `CACHE HIT` for pages already saved under `cache/` and still produce exactly 60 records.

Parser tests (no network):

```bash
PYTHONPATH=src pytest -q
```

## Politeness rules

- **User-agent:** `FlyRankInternshipA9/1.0 (+https://github.com/SairajNarayankar/polite-scraper)` — an honest name plus a contact link.
- **Timeout:** 10 seconds. A request never waits forever.
- **Delay:** at least 500 ms between *real* requests. Cached reads do not sleep.
- **Status check:** only HTTP 200 is treated as a page. Anything else is a failed fetch, not HTML to parse.
- **Cache:** the first successful response is saved under `cache/`. Later runs read the file. The live site should feel a development evening once, not fifty times.
- **Retries:** timeout and 5xx are retried once (backoff + optional `Retry-After`). **404 and 403 are never retried.**
- **One bad page:** each detail URL is handled on its own. A made-up URL is appended on purpose so every run proves `failed_pages: 1` without hammering the real site.

## Record schema

Raw extract (eight fields, always present; `description` may be `null`):

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-16T00:00:00Z"
}
```

Stored record adds `price_gbp` (a number). Identity is the absolute `product_url`. A rerun updates that key — it never appends a duplicate (idempotency).

Pydantic (`src/schema.py`) requires non-empty title / price / availability / rating, `price_gbp > 0`, HTTPS URLs, and an ISO-8601 UTC `fetched_at`. Failures go to `errors.json` with the reason and never enter `books.json`.

## Why this assignment needed no browser

The book title, price, rating, stock line, and description are already in the HTML the server sends. A headless browser would only add startup cost, memory, and flakiness. Use a browser when the facts are missing from the response (for example `quotes.toscrape.com/js`).

## Ethics

Use an official API when one exists. Never bypass logins, paywalls, or blocks. Collect only what you need, say who you are, go slowly, and treat every page as untrusted input until a schema says otherwise. This project is locked to a public practice sandbox.

## Limitation

The selectors are written for Books to Scrape's current markup (`article.product_page`, `div.product_main`, `#product_description`). A redesign would break extraction. The cache also means a long-lived `cache/` folder will not see site changes until those files are deleted.

## Sample run report

First live run (empty cache):

```json
{
  "started_at": "2026-08-15T20:01:47Z",
  "finished_at": "2026-08-15T20:02:24Z",
  "duration_seconds": 37.04,
  "catalogue_pages": 3,
  "discovered": 60,
  "unique_urls": 60,
  "pages_fetched": 63,
  "cache_hits": 1,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

Second run: still **60** records, `cache_hits: 63`, `pages_fetched: 1` (only the deliberate fake URL, which is never cached), `duration_seconds: 1.61`. The fake URL is `https://books.toscrape.com/catalogue/this-book-does-not-exist-a9/index.html` — logged as HTTP 404, not retried.
