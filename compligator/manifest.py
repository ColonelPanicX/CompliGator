"""Authoritative document count manifest for CompliGator.

The manifest is bundled with the package at ``compligator/data/document-manifest.json``
and optionally refreshed from GitHub with a 24-hour TTL cache at
``~/.compligator/manifest-cache.json``.

Usage::

    from compligator.manifest import load_manifest

    manifest = load_manifest()
    entry = manifest.get("fedramp-github")
    if entry is None or entry.dynamic:
        print("count unknown")
    else:
        print(f"expected: {entry.total}")  # e.g. "expected: 9"
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

_SCHEMA_VERSION = 1

_MANIFEST_URL = (
    "https://raw.githubusercontent.com/ColonelPanicX/CompliGator/main"
    "/compligator/data/document-manifest.json"
)

_CACHE_DIR = Path.home() / ".compligator"
_CACHE_FILE = _CACHE_DIR / "manifest-cache.json"
_CACHE_TTL_HOURS = 24

_BUNDLED = Path(__file__).parent / "data" / "document-manifest.json"

# ------------------------------------------------------------------
# Data classes
# ------------------------------------------------------------------


@dataclass(frozen=True)
class FrameworkEntry:
    """Expected document counts for one framework.

    When ``dynamic`` is True, the downloader discovers documents at runtime
    (web crawl, GitHub API, directory scan) and no authoritative total exists.
    ``total``, ``automated``, and ``manual`` will be None in that case.
    """

    total: Optional[int]
    automated: Optional[int]
    manual: Optional[int]
    dynamic: bool = False


@dataclass(frozen=True)
class Manifest:
    """Parsed document count manifest."""

    schema_version: int
    updated: str
    frameworks: dict[str, FrameworkEntry]

    def get(self, key: str) -> Optional[FrameworkEntry]:
        """Return the entry for *key*, or None if the key is not in the manifest."""
        return self.frameworks.get(key)


# ------------------------------------------------------------------
# Parsing
# ------------------------------------------------------------------


def _parse(raw: dict) -> Manifest:
    """Parse a raw JSON dict into a Manifest.

    Raises ValueError if ``schema_version`` does not match ``_SCHEMA_VERSION``.
    """
    if raw.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(
            f"Manifest schema_version {raw.get('schema_version')!r} "
            f"!= expected {_SCHEMA_VERSION}"
        )
    frameworks: dict[str, FrameworkEntry] = {}
    for key, entry in raw.get("frameworks", {}).items():
        frameworks[key] = FrameworkEntry(
            total=entry.get("total"),
            automated=entry.get("automated"),
            manual=entry.get("manual"),
            dynamic=entry.get("dynamic", False),
        )
    return Manifest(
        schema_version=raw["schema_version"],
        updated=raw.get("updated", ""),
        frameworks=frameworks,
    )


# ------------------------------------------------------------------
# Loading strategies
# ------------------------------------------------------------------


def _load_bundled() -> Manifest:
    """Load the manifest bundled with the package. Always succeeds."""
    raw = json.loads(_BUNDLED.read_text(encoding="utf-8"))
    return _parse(raw)


def _load_cached() -> Optional[Manifest]:
    """Return the cached manifest if it is fresh and schema-compatible, else None."""
    if not _CACHE_FILE.exists():
        return None
    try:
        age_hours = (datetime.now(timezone.utc).timestamp() - _CACHE_FILE.stat().st_mtime) / 3600
        if age_hours > _CACHE_TTL_HOURS:
            return None
        raw = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        return _parse(raw)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        log.debug("Manifest cache invalid, ignoring: %s", exc)
        return None


def _fetch_remote() -> Optional[Manifest]:
    """Fetch the manifest from GitHub and write it to the cache.

    Returns None on any network or parse error without raising.
    """
    try:
        req = Request(
            _MANIFEST_URL,
            headers={"User-Agent": "CompliGator/manifest-refresh"},
        )
        with urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
        raw = json.loads(body)
        manifest = _parse(raw)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, _CACHE_FILE)
        log.debug("Manifest refreshed from GitHub (%s)", manifest.updated)
        return manifest
    except (URLError, OSError, json.JSONDecodeError, ValueError) as exc:
        log.debug("Manifest remote fetch failed: %s", exc)
        return None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def load_manifest() -> Manifest:
    """Load the authoritative document count manifest.

    Resolution order:

    1. Cache (``~/.compligator/manifest-cache.json``) — if < 24 h old and
       ``schema_version`` matches.
    2. GitHub raw URL — fetched with a 5 s timeout; cached on success.
    3. Bundled file (``compligator/data/document-manifest.json``) — always
       available offline.

    The function never raises. In the worst case it returns the bundled manifest.
    """
    cached = _load_cached()
    if cached is not None:
        return cached

    remote = _fetch_remote()
    if remote is not None:
        return remote

    return _load_bundled()
