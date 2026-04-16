"""MITRE ATT&CK downloader.

Downloads STIX 2.1 JSON for Enterprise ATT&CK, ICS ATT&CK, and Mobile ATT&CK
from the mitre-attack/attack-stix-data GitHub repository releases.

Uses the GitHub Releases API to discover the latest tagged release and download
its assets. Set the GITHUB_TOKEN environment variable to raise the
unauthenticated API rate limit from 60 to 5,000 requests/hour.

Note: ATT&CK STIX files are large (50–200 MB combined). State tracking is used
to skip re-downloading files that have not changed since the last sync.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    DownloadResult,
    download_file,
)

RELEASES_API_URL = "https://api.github.com/repos/mitre-attack/attack-stix-data/releases/latest"
SOURCE_URL = "https://github.com/mitre-attack/attack-stix-data"

# File extensions to download from release assets
DOWNLOAD_EXTENSIONS = {".json"}

# Date the KNOWN_DOCS list was last manually verified against the latest release
KNOWN_DOCS_VERIFIED = "2026-03-02"

# Curated fallback — used if the GitHub API is unavailable.
# Pinned to v18.1 (November 2025). Update when a new ATT&CK version is released.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "enterprise-attack.json",
        "https://github.com/mitre-attack/attack-stix-data/releases/download/v18.1/enterprise-attack.json",
    ),
    (
        "ics-attack.json",
        "https://github.com/mitre-attack/attack-stix-data/releases/download/v18.1/ics-attack.json",
    ),
    (
        "mobile-attack.json",
        "https://github.com/mitre-attack/attack-stix-data/releases/download/v18.1/mobile-attack.json",
    ),
]


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _api_headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_latest_assets() -> list[tuple[str, str]]:
    """Return (filename, download_url) for all STIX JSON release assets.

    Raises RuntimeError on API errors.
    """
    try:
        resp = requests.get(RELEASES_API_URL, headers=_api_headers(), timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"GitHub API request failed: {exc}") from exc

    if resp.status_code == 403:
        raise RuntimeError(
            "GitHub API rate-limited. "
            "Set GITHUB_TOKEN env var to increase the unauthenticated limit."
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f"GitHub API returned {resp.status_code} for mitre-attack/attack-stix-data"
        )

    data = resp.json()
    tag = data.get("tag_name", "unknown")
    assets = [
        (asset["name"], asset["browser_download_url"])
        for asset in data.get("assets", [])
        if Path(asset["name"]).suffix.lower() in DOWNLOAD_EXTENSIONS
    ]
    if not assets:
        raise RuntimeError(f"No JSON assets found in release {tag}")
    return assets


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "mitre-attack"
    result = DownloadResult(framework="mitre-attack")

    docs: list[tuple[str, str]]
    used_known = False
    try:
        docs = _fetch_latest_assets()
    except RuntimeError as exc:
        result.notices.append(
            f"GitHub API unavailable ({exc}) — using curated fallback list "
            f"(last verified {KNOWN_DOCS_VERIFIED}, pinned to v18.1)."
        )
        docs = KNOWN_DOCS
        used_known = True

    if dry_run:
        for filename, _url in docs:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    print("  [i] ATT&CK STIX files are large (50–200 MB). Download may take several minutes.")
    session = requests.Session()

    for filename, url in docs:
        target = dest / filename
        # Large files: use a generous timeout via the session directly
        ok, msg = download_file(session, url, target, force=force, state=state)
        if msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            if used_known:
                result.errors.append((filename, msg))
            else:
                result.errors.append((filename, f"{msg} ({url})"))

    return result
