# FL-07 Build log — My First Agent (Gumloop)

**Intern:** Sairaj Narayankar  
**Assignment:** FL-07 · Build the Agent · Checkpoint 1 (MVP)  
**Track:** General AI Fluency · Week 5  
**Platform (FL-06):** Gumloop custom agent  
**Agent:** [My First Agent](https://gumloop.com/agents/fZcFR74FWkSjqMyqvvS6tB)  
**Proof chat (this run):** https://gumloop.com/agents/fZcFR74FWkSjqMyqvvS6tB/chat/qv2Af2sgznhs7ZkrJYWELD  
**Earlier related chat (A9 scraper, not this MVP):** https://gumloop.com/agents/fZcFR74FWkSjqMyqvvS6tB/chat/48zn3PjYAtG61carhEfjPH  
**Public artifact:** https://github.com/SairajNarayankar/polite-scraper  

This log is written from the actual Checkpoint 1 run on 16 Aug 2026 (IST). Failures stay in the story.

---

## 1. What I set out to build

Narrowest core job I would accept as “done”:

> Given a public GitHub repo URL, produce a one-page repo brief from live tools: what it is, latest commit, real top-level files, how to run it, and one risk.

That is one full loop: **request → GitHub + Firecrawl → brief**. No dashboard, no RAG, no issue triage, no second repo.

Live connections used:

| Connection | Role |
| --- | --- |
| GitHub | `list_commits`, `get_contents` on `SairajNarayankar/polite-scraper` |
| Firecrawl | Scrape the public repo page; confirm HTTP 200 and latest commit |

---

## 2. What I cut, and why I changed the first plan

FL-07 says: build on the FL-06 platform, start with the **narrowest** version of the core job, get one end-to-end run working before adding anything.

I already had a working A9 scraper on this same agent (`polite-scraper`, chat `48zn3PjYAtG61carhEfjPH`). That chat even committed a `BUILD_LOG.md` titled FL-07. Treating “ship another scraper” as Checkpoint 1 would have been a second product, not a first working agent loop.

**Deviation from that earlier write-up:** Checkpoint 1 core job is the **repo brief**, not the A9 pipeline. The scraper is the *subject* of the brief. I kept the existing `BUILD_LOG.md` on the repo (do not rewrite history as if the first attempt never happened) and added this log as a separate file.

I also did **not** record the 2-minute screen capture from inside the agent. That has to be recorded on my machine. Script is in §6.

---

## 3. Iteration (what actually broke)

### 3.1 Assignment page is behind login

`Web Fetch` on `https://internship.flyrank.ai/intern/assignments/FL-07` returned the LinkedIn sign-in page, not the spec. I worked from the screenshot the intern pasted (Checkpoint 1, live tool required, honest build log, unedited run capture).

### 3.2 `get_contents(..., recursive=true)` crashed

First GitHub directory call used `recursive: true`. The connector raised:

```
TypeError: Repository.get_contents() got an unexpected keyword argument 'recursive'
```

**Change:** drop `recursive`. Call `path: "."` only.

**Result:** root listing returned the eight real entries listed in the brief.

### 3.3 Oversized GitHub / Firecrawl payloads

`list_repositories`, `list_commits`, and `firecrawl__scrape` all spilled to disk (`OUTPUT TOO LARGE`). I did not invent SHAs from memory. I parsed the spill files in Python and printed only `date / short SHA / message`.

Latest commit extracted that way: `fb5fb00` · `2026-08-15T21:15:29Z` · `Docs: add FL-07 honest build log`.

### 3.4 Firecrawl did work

`firecrawl__scrape` on `https://github.com/SairajNarayankar/polite-scraper` returned `statusCode: 200` and the same latest-commit line the API returned. That is the live reachability check.

### 3.5 Scope temptation

The intern’s screenshot says “everything else in your submission orbits” the working agent. I almost expanded into issue triage or a dashboard. I cut that. One request → one brief.

---

## 4. End-to-end proof (no mid-run hand-edit)

From this chat, without pasting file lists or commit SHAs by hand:

1. Intern uploaded the FL-07 assignment screenshot.
2. Agent connected GitHub + Firecrawl (already on the agent from FL-06).
3. Agent listed live commits and root contents; Firecrawl confirmed the public page.
4. Agent wrote `REPO-BRIEF.md` from those tool results.

Human actions that stay required:

- Recording the ~2 minute unedited screen capture (§6).
- Pasting the public links into the FlyRank form.

No mid-run editing of the GitHub file list. No invented SHA.

---

## 5. How this maps to FL-07 criteria

| Criterion | Evidence |
| --- | --- |
| Core job end to end, no mid-run hand-editing | This chat + `REPO-BRIEF.md` |
| At least one live tool / data connection | GitHub `list_commits` + `get_contents`; Firecrawl scrape (HTTP 200) |
| Matches FL-06 / deviations documented | Platform = Gumloop. First draft of “FL-07” on the scraper repo was too wide; this log records the cut |
| Build log shows real iteration | Login wall, `recursive` TypeError, oversized payloads |
| Unedited run capture | Recorded separately. Script in §6 |

---

## 6. Screen-capture script (~2 minutes, unedited)

Record the whole thing in one take. Do not cut.

1. Open this chat: https://gumloop.com/agents/fZcFR74FWkSjqMyqvvS6tB/chat/qv2Af2sgznhs7ZkrJYWELD
2. Scroll the visible GitHub + Firecrawl tool steps (commits, root listing, scrape 200).
3. Scroll to the finished repo brief in the agent reply.
4. Open https://github.com/SairajNarayankar/polite-scraper — show latest commit `fb5fb00` and the root files matching the brief.
5. Open `FL-07-BUILD-LOG.md` on the repo (this file) and scroll the failure section (`recursive` TypeError).

Stop. That is the loop: request → live tools → brief.
