from __future__ import annotations

import json
import urllib.error
import urllib.request

DEFAULT_USER_AGENT = 'JobeasyBot/1.0 (+https://jobeas.com)'


def fetch_json(url: str, *, timeout: int = 30) -> dict | list:
    request = urllib.request.Request(
        url,
        headers={'User-Agent': DEFAULT_USER_AGENT, 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'HTTP {exc.code} for {url}: {body[:500]}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Failed to reach {url}: {exc.reason}') from exc
