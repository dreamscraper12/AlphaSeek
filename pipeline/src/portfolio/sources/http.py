"""Minimal HTTP GET helper. Adapters take a `fetch` callable so tests can
inject a fake transport instead of hitting real providers over the network."""

from __future__ import annotations

import json
import urllib.request
from typing import Callable

Fetcher = Callable[[str], bytes]


def urlopen_fetcher(url: str, timeout: float = 10.0) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str, fetch: Fetcher = urlopen_fetcher) -> dict:
    return json.loads(fetch(url))
