# Repo brief — SairajNarayankar/polite-scraper

**Source:** live GitHub API + Firecrawl scrape of the public repo page  
**Checked:** 2026-08-15 21:30 UTC (2026-08-16 03:00 IST)  
**URL:** https://github.com/SairajNarayankar/polite-scraper

## 1. What it is

`polite-scraper` is a small Python pipeline for the public practice site [Books to Scrape](https://books.toscrape.com/). It walks the first three catalogue pages, visits 60 book pages, turns HTML into schema-checked JSON, skips one deliberate broken URL without crashing, and writes an honest run report. It is the public artifact from FlyRank Backend Week 5 A9, not a general-purpose crawler.

## 2. Latest commit (live GitHub)

| Field | Value |
| --- | --- |
| SHA | `fb5fb005f572f00c8f7fba14d7471ca5f05a80ee` |
| Date | 2026-08-15T21:15:29Z |
| Message | Docs: add FL-07 honest build log |
| Author | Sairaj Narayankar |

Firecrawl scrape of the public page returned **HTTP 200** and showed the same latest commit (`fb5fb00`, same message). The page is reachable.

## 3. Top-level layout (live `get_contents` on `.`)

| Name | Type |
| --- | --- |
| `.gitignore` | file |
| `BUILD_LOG.md` | file |
| `LICENSE` | file |
| `README.md` | file |
| `output/` | dir |
| `requirements.txt` | file |
| `src/` | dir |
| `tests/` | dir |

No other root entries were returned. I did not invent folders.

## 4. How a stranger would run it

Documented in the README quick start:

```bash
git clone https://github.com/SairajNarayankar/polite-scraper.git
cd polite-scraper
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

Parser tests (no network): `PYTHONPATH=src pytest -q`

Dependencies from live `requirements.txt`: `requests`, `beautifulsoup4`, `pydantic`, `pytest`. Python 3.10+.

Expected outputs: `output/books.json` (60 records), `output/run-report.json`, `output/errors.json`. A second run should print cache hits.

## 5. One concrete risk

Selectors are locked to Books to Scrape’s current markup (`article.product_page`, `div.product_main`, `#product_description`). A site redesign breaks extraction. A leftover `cache/` folder will also hide site changes until those files are deleted.

---

This brief is the Checkpoint 1 core-job output. One request → one brief. No dashboard, no second repo.
