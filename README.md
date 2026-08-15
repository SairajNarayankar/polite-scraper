<div align="center">

# The Polite Scraper

**Fetch → extract → normalize → validate → store → report.**

A small, respectful scraping pipeline for [Books to Scrape](https://books.toscrape.com/).  
It walks the first three catalogue pages, visits all 60 book pages, turns messy HTML into schema-checked JSON, skips a broken page without crashing, and ends every run with an honest report.

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Requests](https://img.shields.io/badge/http-requests-2CA5E0)](https://requests.readthedocs.io/)
[![Beautiful Soup](https://img.shields.io/badge/html-beautifulsoup4-8BC34A)](https://www.crummy.com/software/BeautifulSoup/)
[![Pydantic](https://img.shields.io/badge/schema-pydantic-E92063)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)
[![FlyRank A9](https://img.shields.io/badge/FlyRank-W5%20A9-111827)](https://github.com/SairajNarayankar/polite-scraper)

[Quick start](#-quick-start) · [Pipeline](#-pipeline) · [Target](#-target-classification) · [Schema](#-record-schema) · [Report](#-sample-run-report)

</div>

---

## Table of contents

- [Why this exists](#-why-this-exists)
- [Features](#-features)
- [Quick start](#-quick-start)
- [What you get](#-what-you-get)
- [Pipeline](#-pipeline)
- [Project layout](#-project-layout)
- [Target classification](#-target-classification)
- [Politeness rules](#-politeness-rules)
- [Record schema](#-record-schema)
- [Failure handling](#-failure-handling)
- [Tests](#-tests)
- [Sample run report](#-sample-run-report)
- [Why no browser](#-why-this-assignment-needed-no-browser)
- [Ethics](#-ethics)
- [Limitation](#-limitation)
- [License](#-license)

---

## Why this exists

Almost every AI system starts with the same question: *where does the data come from?* A model should not re-read a web page every day just to find a price. Something has to collect that data first — reliably and respectfully.

This repo is that something, built for **FlyRank Internship · Backend Track · Week 5 · Assignment A9**.

Three habits, in this order:

1. **Check before you collect.** Classify the target before writing request code.
2. **Be a polite guest.** Say who you are, go slowly, never hammer a site.
3. **Trust nothing you scraped.** A web page is untrusted input until a schema says otherwise.

---

## Features

| | |
| --- | --- |
| **Polite fetch** | Honest user-agent, 10s timeout, 500ms delay, status-200 only |
| **Disk cache** | First hit saves HTML; later runs print `CACHE HIT` and skip the network |
| **Catalogue crawl** | Follows the site's own `next` link for 3 pages — no hardcoded book URLs |
| **Clean extract** | Selectors aimed at the product area, not the whole document |
| **Normalize** | `£51.77` → `price_gbp: 51.77`; relative links → absolute HTTPS URLs |
| **Validate** | Pydantic schema; bad rows go to `errors.json`, never `books.json` |
| **Idempotent** | Canonical identity is `product_url`. A rerun updates — it never duplicates |
| **Survives failure** | One fake 404 is skipped on purpose; the other 60 records still land |
| **Honest report** | Start time, duration, fetches, cache hits, valid / invalid / failed |

---

## Quick start

A stranger should be able to clone this and get `books.json` in under five minutes.

```bash
git clone https://github.com/SairajNarayankar/polite-scraper.git
cd polite-scraper
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

**Lane:** Python 3.10+ · Requests · Beautiful Soup · Pydantic.

Parser tests (no network):

```bash
PYTHONPATH=src pytest -q
```

---

## What you get

| File | Meaning |
| --- | --- |
| `output/books.json` | 60 validated, unique records |
| `output/errors.json` | Schema failures with a reason (empty on a clean run) |
| `output/run-report.json` | Counts, cache hits, failures, duration |
| `cache/` | Saved HTML for development — **gitignored** |

A second run should print `CACHE HIT` for pages already on disk and still produce **exactly 60** records.

---

## Pipeline

```
classify  →  fetch + cache  →  extract  →  normalize  →  validate  →  store  →  report
   │              │               │            │             │           │         │
 README      status 200 only   8 raw keys   price_gbp    Pydantic   books.json  run-report
 robots.txt   500ms delay      null, never   absolute     fails →    keyed by    honest
              disk cache       invented      URLs         errors.json product_url numbers
```

That table is the assignment — roughly one stage per row.

---

## Project layout

```
polite-scraper/
├── README.md
├── requirements.txt
├── .gitignore              # cache/ is ignored
├── src/
│   ├── main.py             # discover → scrape → validate → report
│   ├── fetch.py            # user-agent, timeout, cache, retry
│   ├── extract.py          # catalogue + book selectors
│   └── schema.py           # Pydantic BookRecord
├── tests/
│   ├── test_extract.py     # 7 fixture tests, no live network
│   └── fixtures/
└── output/                 # sample books.json + run-report.json
```

---

## Target classification

| Question | Answer |
| --- | --- |
| **Which site?** | [Books to Scrape](https://books.toscrape.com/), listed on [toscrape.com](https://toscrape.com/) |
| **Why this site?** | ToScrape describes it as a fictional bookstore that *desperately wants to be scraped* — a public practice sandbox for beginners and for validating scrapers. That sentence is the permission. |
| **How much?** | The first **3 catalogue pages only** (20 books each → 60 detail pages). The crawler follows the site's own `next` link and then stops. |
| **What data?** | Title, product URL, price (raw text + `price_gbp`), availability, star rating, description (or `null`), plus provenance (`source_page`, `fetched_at`). |
| **Why is that appropriate?** | The site exists so people can practise this exact skill. The scope is tiny, the data is fictional, and nothing personal or gated is collected. |

**robots.txt check (2026-08-16):** `GET https://books.toscrape.com/robots.txt` returned **HTTP 404**. Result written down as: **no robots file found**. A missing file is not permission — it is just a missing file. Permission here comes from the sandbox's own statement on toscrape.com, not from a robots file.

> I will not reuse this code on another site without checking its rules and terms first.

---

## Politeness rules

| Rule | What this repo does |
| --- | --- |
| **User-agent** | `FlyRankInternshipA9/1.0 (+https://github.com/SairajNarayankar/polite-scraper)` — an honest name plus a contact link |
| **Timeout** | 10 seconds. A request never waits forever |
| **Delay** | ≥ 500 ms between *real* requests. Cached reads do not sleep |
| **Status** | Only HTTP **200** is a page. Anything else is a failed fetch, not HTML to parse |
| **Cache** | First successful response is saved under `cache/`. The live site should feel a development evening **once**, not fifty times |
| **Retries** | Timeout and 5xx are retried once (backoff + optional `Retry-After`). **404 and 403 are never retried** |
| **One bad page** | Each detail URL is handled on its own. A made-up URL is appended on purpose so every run proves `failed_pages: 1` without hammering the real site |

---

## Record schema

Raw extract — eight fields, always present. `description` may be `null`. Never invented.

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

Stored record adds `price_gbp` (a number). Identity is the absolute `product_url`. A rerun updates that key — it never appends a duplicate (**idempotency**).

Pydantic (`src/schema.py`) requires:

- non-empty `title`, `price_text`, `availability_text`, `rating_text`
- `price_gbp > 0`
- HTTPS `product_url` and `source_page`
- ISO-8601 UTC `fetched_at` (`YYYY-MM-DDTHH:MM:SSZ`)

Failures go to `errors.json` with the reason and never enter `books.json`.

---

## Failure handling

A good job finishes its work, then tells you what happened.

- Each page is handled separately. Fifty-nine good records survive one bad one.
- Timeout / 5xx → wait and try **once**. 404 / 403 → log and skip.
- Proof: every run appends  
  `https://books.toscrape.com/catalogue/this-book-does-not-exist-a9/index.html`  
  Break things on our side only — never test failure by hammering the real site.

---

## Tests

Seven unit tests, all offline, using small HTML fixtures:

| Test | Proves |
| --- | --- |
| Price normalization | `£51.77` → `51.77` |
| Relative → absolute URL | `urljoin`, never string glue |
| Missing description | stored as `null`, not invented |
| Extra whitespace | availability text is collapsed |
| Duplicate URLs | collapsed with `dict.fromkeys` |
| Malformed fixture | fails the schema |
| Valid fixture | passes the schema |

```bash
PYTHONPATH=src pytest -q
# 7 passed
```

---

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

Second run: still **60** records, `cache_hits: 63`, `pages_fetched: 1` (only the deliberate fake URL, which is never cached), `duration_seconds: 1.61`. The fake URL logged as **HTTP 404**, not retried.

---

## Why this assignment needed no browser

The book title, price, rating, stock line, and description are already in the HTML the server sends. A headless browser would only add startup cost, memory, and flakiness. Use a browser when the facts are missing from the response (for example [`quotes.toscrape.com/js`](https://quotes.toscrape.com/js)).

---

## Ethics

- Use an official API when one exists.
- Never bypass logins, paywalls, or blocks.
- Collect only what you need.
- Say who you are. Go slowly.
- Treat every page as untrusted input until a schema says otherwise.

This project is locked to a public practice sandbox.

---

## Limitation

Selectors are written for Books to Scrape's current markup (`article.product_page`, `div.product_main`, `#product_description`). A redesign would break extraction. A long-lived `cache/` folder will not see site changes until those files are deleted.

---

## License

MIT. See [LICENSE](./LICENSE).

Built for the FlyRank Backend Track. The only target is a public practice sandbox; all linked resources are free.
