"""Polite HTTP fetch with disk cache, timeout, status checks, and one retry."""

from __future__ import annotations

import hashlib
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/SairajNarayankar/polite-scraper)"
)
TIMEOUT_SECONDS = 10
MIN_DELAY_SECONDS = 0.5
MAX_ATTEMPTS = 2  # first try + one retry for timeout / 5xx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"


@dataclass
class FetchResult:
    url: str
    html: str | None
    status_code: int | None
    from_cache: bool
    bytes: int
    fetched_at: str  # ISO-8601 UTC
    error: str | None = None
    attempts: int = 1


def _cache_path(url: str) -> Path:
    """Stable on-disk name. Catalogue pages keep the assignment's filenames."""
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if re.fullmatch(r"page-\d+\.html", name):
        return CACHE_DIR / f"catalogue-{name}"
    if name == "index.html" and parsed.path in ("/", "/index.html"):
        return CACHE_DIR / "catalogue-page-1.html"
    slug = parsed.path.strip("/").replace("/", "__") or "root"
    if len(slug) > 180:
        slug = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / "books" / f"{slug}.html"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _mtime_utc(path: Path) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime))


def polite_pause(from_cache: bool) -> None:
    if from_cache:
        return
    time.sleep(MIN_DELAY_SECONDS)


def fetch_page(
    url: str,
    session: requests.Session | None = None,
    stats: dict | None = None,
) -> FetchResult:
    """
    Return cached HTML when present. Otherwise request the URL politely.

    Only status 200 is treated as a successful page. Timeouts and 5xx are
    retried once. 403 and 404 are never retried.
    """
    cache_path = _cache_path(url)
    if cache_path.exists():
        html = cache_path.read_text(encoding="utf-8", errors="replace")
        result = FetchResult(
            url=url,
            html=html,
            status_code=200,
            from_cache=True,
            bytes=len(html.encode("utf-8")),
            fetched_at=_mtime_utc(cache_path),
            attempts=0,
        )
        print(f"CACHE HIT  url={url} bytes={result.bytes}")
        if stats is not None:
            stats["cache_hits"] = stats.get("cache_hits", 0) + 1
        return result

    client = session or requests.Session()
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    last_error: str | None = None
    last_status: int | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            last_status = response.status_code
            print(
                f"FETCH      url={url} status={response.status_code} "
                f"attempt={attempt} bytes={len(response.content)}"
            )
            if stats is not None:
                stats["pages_fetched"] = stats.get("pages_fetched", 0) + 1

            if response.status_code == 200:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(response.content)
                html = response.content.decode("utf-8", errors="replace")
                return FetchResult(
                    url=url,
                    html=html,
                    status_code=200,
                    from_cache=False,
                    bytes=len(response.content),
                    fetched_at=_utc_now(),
                    attempts=attempt,
                )

            # Do not retry client refusals or missing pages.
            if response.status_code in (403, 404) or 400 <= response.status_code < 500:
                return FetchResult(
                    url=url,
                    html=None,
                    status_code=response.status_code,
                    from_cache=False,
                    bytes=len(response.content),
                    fetched_at=_utc_now(),
                    error=f"HTTP {response.status_code}",
                    attempts=attempt,
                )

            last_error = f"HTTP {response.status_code}"
            retry_after = response.headers.get("Retry-After")
            if attempt < MAX_ATTEMPTS:
                wait = _retry_wait(retry_after, attempt)
                print(f"RETRY      url={url} wait={wait:.2f}s reason={last_error}")
                time.sleep(wait)
        except requests.Timeout:
            last_error = "timeout"
            print(f"FETCH      url={url} status=timeout attempt={attempt}")
            if stats is not None:
                stats["pages_fetched"] = stats.get("pages_fetched", 0) + 1
            if attempt < MAX_ATTEMPTS:
                wait = _retry_wait(None, attempt)
                print(f"RETRY      url={url} wait={wait:.2f}s reason=timeout")
                time.sleep(wait)
        except requests.RequestException as exc:
            last_error = f"request_error: {exc.__class__.__name__}"
            print(f"FETCH      url={url} status=error attempt={attempt} err={last_error}")
            if stats is not None:
                stats["pages_fetched"] = stats.get("pages_fetched", 0) + 1
            if attempt < MAX_ATTEMPTS:
                wait = _retry_wait(None, attempt)
                print(f"RETRY      url={url} wait={wait:.2f}s reason={last_error}")
                time.sleep(wait)

    return FetchResult(
        url=url,
        html=None,
        status_code=last_status,
        from_cache=False,
        bytes=0,
        fetched_at=_utc_now(),
        error=last_error or "unknown_fetch_error",
        attempts=MAX_ATTEMPTS,
    )


def _retry_wait(retry_after: str | None, attempt: int) -> float:
    """Honor Retry-After when present; otherwise exponential backoff + jitter."""
    if retry_after:
        try:
            return max(0.5, float(retry_after))
        except ValueError:
            pass
    return (2 ** (attempt - 1)) + random.uniform(0, 0.25)
