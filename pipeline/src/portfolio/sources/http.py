"""Minimal HTTP GET helper. Adapters take a `fetch` callable so tests can
inject a fake transport instead of hitting real providers over the network."""

from __future__ import annotations

import json
import urllib.request
from typing import Callable

Fetcher = Callable[[str], bytes]

# Identify the client honestly to every provider. Some (Yahoo) reject the
# default urllib agent outright; the rest simply deserve to know who is
# calling them.
USER_AGENT = 'AlphaSeek-portfolio-pipeline/0.1'


def urlopen_fetcher(url: str, timeout: float = 10.0) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str, fetch: Fetcher = urlopen_fetcher) -> dict:
    return json.loads(fetch(url))
