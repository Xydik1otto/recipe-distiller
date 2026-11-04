"""HTTP fetching with retries and a mobile-UA fallback."""

from __future__ import annotations

from typing import Optional

import httpx

from .extractor import DESKTOP_UA, MOBILE_UA

RETRY_STATUS = {403, 429, 500, 502, 503, 504}


def fetch_html(url: str, max_attempts: int = 3, timeout: float = 20.0) -> str:
    """Fetch a page; retry on transient failures, falling back to mobile UA."""
    last_error: Optional[Exception] = None
    for attempt in range(max_attempts):
        ua = DESKTOP_UA if attempt < max_attempts - 1 else MOBILE_UA
        headers = {"User-Agent": ua,
                   "Accept": "text/html,application/xhtml+xml",
                   "Accept-Language": "en-US,en;q=0.9,uk;q=0.8"}
        try:
            resp = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            if resp.status_code in RETRY_STATUS:
                last_error = httpx.HTTPStatusError(
                    f"status {resp.status_code}", request=resp.request, response=resp)
                continue
            resp.raise_for_status()
            return resp.text
        except (httpx.HTTPError, httpx.HTTPStatusError) as e:
            last_error = e
            continue
    raise RuntimeError(f"failed to fetch {url} after {max_attempts} attempts: {last_error}")
