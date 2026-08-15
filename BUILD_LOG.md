# FL-07 Build log — My First Agent (Gumloop)

**Intern:** Sairaj Narayankar  
**Assignment:** FL-07 · Build the Agent · Checkpoint 1 (MVP)  
**Track:** General AI Fluency · Week 5  
**Platform (FL-06):** Gumloop custom agent  
**Agent:** [My First Agent](https://gumloop.com/agents/fZcFR74FWkSjqMyqvvS6tB)  
**Proof chat:** https://gumloop.com/agents/fZcFR74FWkSjqMyqvvS6tB/chat/48zn3PjYAtG61carhEfjPH  
**Public artifact:** https://github.com/SairajNarayankar/polite-scraper  

This log is written from the actual run, not reconstructed after the fact. Times are IST / UTC from 16 Aug 2026.

---

## 1. What I set out to build

Narrowest core job I would accept as “done”:

> Given a scraping assignment brief, classify the target, fetch the first three catalogue pages of Books to Scrape, extract and validate 60 book records, survive one broken page, and publish a public GitHub repo a stranger can run.

That is one full loop: **request → live tools → files → GitHub**. No extra dashboards, no AI rematch, no CSV export.

Live connections used:

| Connection | Role |
| --- | --- |
| Firecrawl | Read toscrape.com permission page + robots.txt + sample HTML |
| GitHub | Create/update files on `SairajNarayankar/polite-scraper` |
| Sandbox (Python) | Build, test, and run the scraper against the live sandbox site |

---

## 2. What I cut from a bigger spec

A9 also lists stretch items (CSV, change detection, dashboard, Playwright vs HTTP, Ollama enrichment, AI rematch). I cut all of them for Checkpoint 1.

**Why:** FL-07 says start with the narrowest version of the core job and get one end-to-end run working before adding anything. Stretch work would have delayed the first green run and the GitHub push.

I also did **not** record the screen from inside the agent. A 2-minute unedited capture has to be recorded on my machine while I replay the loop. The chat URL is the machine-readable trail; the video is the human one.

---

## 3. Iteration (what actually broke)

### 3.1 Target check first (this worked)

Opened [toscrape.com](https://toscrape.com/) via Firecrawl. The page calls Books to Scrape a fictional bookstore that “desperately wants to be scraped.” That is the permission.

`GET https://books.toscrape.com/robots.txt` → **HTTP 404**. Wrote down “no robots file found.” A missing file is not permission.

### 3.2 Unit tests failed twice on URL joining

I first assumed catalogue links look like `../book/index.html`. Live page-1 HTML uses `a-light-in-the-attic_1000/index.html` (same directory). The fixture was wrong, not `urljoin`.

Then I “fixed” the test by joining `../book/...` against `https://books.toscrape.com/index.html` and expected `/catalogue/...`. That is also wrong — `urljoin` correctly produces `/book/...`.

Then I tried a nested category base and expected `/catalogue/book`. `urljoin` produced `/catalogue/category/book`.

**Change:** Stop inventing path shapes. Test the two joins the crawler actually uses: `page-2.html` and `book/index.html` against `catalogue/page-1.html`.

**Result:** `7 passed`.

### 3.3 Cache directory owned by root

First catalogue fetch wrote `cache/catalogue-page-1.html` as root. The next write (`catalogue-page-2.html`) raised:

```
PermissionError: [Errno 13] Permission denied: '.../cache/catalogue-page-2.html'
```

**Change:** `chown` the cache back to the sandbox user. Do not fetch as a privileged process into a shared folder.

**Result:** first live run finished.

```
catalogue_pages=3 discovered=60 unique_urls=60
REPORT  valid=60 invalid=0 failed_pages=1 fetched=63 cache_hits=1 duration_s=37.04
```

The failed page is the deliberate fake URL  
`https://books.toscrape.com/catalogue/this-book-does-not-exist-a9/index.html`  
logged as HTTP 404, **not retried**.

### 3.4 Second run proved the cache

```
REPORT  valid=60 invalid=0 failed_pages=1 fetched=1 cache_hits=63 duration_s=1.61
```

Still 60 records. Only the fake 404 left the machine. Idempotent.

### 3.5 GitHub was not connected

`create_repository` was not available until the intern connected GitHub on this agent (`add_server_awaiter`). That is a real gate, not a code bug.

### 3.6 Repo name already existed

`github__create_repository` returned 422: *name already exists on this account*. The repo had only a LICENSE (initial commit `e2f9774`).

**Change:** Do not create a second repo. Commit onto the existing public URL the intern asked for.

Pushed seven stage commits on `main`:

| SHA | Message |
| --- | --- |
| `5e7facd` | Stage 0: classify scraping target |
| `a03f5d2` | Stage 1: fetch and cache HTML |
| `2f82400` | Stage 2: discover three catalogue pages |
| `9e1f425` | Stage 3: extract book details |
| `5b2a5e0` | Stage 4: validate normalized records |
| `498342c` | Stage 5: survive failures, report the run |
| `c93fd52` | Stage 6: publish scraper evidence |

Then `dd3b42d` — README rewrite (requested after the first push).

`cache/` is gitignored. Sample `output/books.json` (60 records) is in the repo.

---

## 4. End-to-end proof (no mid-run hand-edit)

From one chat, without pasting HTML into the agent by hand:

1. Assignment brief uploaded.
2. Agent classified the target and robots result.
3. Agent wrote the scraper, fixed its own tests, ran against the live site.
4. Agent connected GitHub after auth, then published the repo.

Human actions that *were* required (and should stay required):

- Connecting the GitHub integration when the agent asked.
- Recording the 2-minute screen capture (below).
- Pasting links into the FlyRank submission form.

No mid-run editing of `books.json`. No manual copy of 60 URLs.

---

## 5. How this maps to FL-07 criteria

| Criterion | Evidence |
| --- | --- |
| Core job end to end, no mid-run hand-editing | Chat + `output/books.json` + GitHub history |
| At least one live tool / data connection | Firecrawl + GitHub + live Books to Scrape |
| Matches FL-06 / deviations documented | Platform = Gumloop. Scope narrowed to one job (scrape → validate → publish). Stretch A9 extras cut — see §2 |
| Build log shows real iteration | Failed URL tests, root-owned cache, 422 on repo create |
| Unedited run capture | Recorded separately (~2 min). Script in §6 |

---

## 6. Screen-capture script (~2 minutes, unedited)

Record the whole thing in one take. Do not cut.

1. Open the public repo. Scroll README (target classification + robots 404).
2. `git log --oneline` — show the seven stage commits.
3. Clone into a fresh folder (or use the existing checkout).
4. `python src/main.py` — second run is fine: `CACHE HIT`, `valid=60`, `failed_pages=1`.
5. Open `output/run-report.json` and one record in `books.json`.
6. Open the Gumloop chat URL and scroll the Firecrawl + GitHub tool steps.

If the reviewer wants a cold-cache fetch, delete `cache/` first. That run takes ~40s; still under two minutes if you start recording at `python src/main.py`.
