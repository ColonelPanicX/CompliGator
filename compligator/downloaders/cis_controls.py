"""CIS Controls v8 structured data downloader.

Downloads the CIS Controls Assessment Specification from the CISecurity
GitHub organization as a repository archive (ZIP). The archive contains
reStructuredText (.rst) control specifications organized by control number
(control-1 through control-18), covering all CIS Controls v8 safeguards.

Note: The structured data format is reStructuredText, not YAML/JSON. The
formatted CIS Controls v8 PDF requires a free CIS WorkBench account and is
not available for automated download (see manual acquisition issue).

Source: github.com/CISecurity/ControlsAssessmentSpecification
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

REPO_OWNER = "CISecurity"
REPO_NAME = "ControlsAssessmentSpecification"
SOURCE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
ARCHIVE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/main.zip"
RELEASES_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-03"

KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "CIS-ControlsAssessmentSpecification-main.zip",
        ARCHIVE_URL,
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


def _fetch_release_archive() -> list[tuple[str, str]]:
    """Try the latest GitHub release for a downloadable archive asset.

    Falls back to the main branch ZIP if no release assets exist.
    Raises RuntimeError on API failure.
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
    if resp.status_code == 404:
        raise RuntimeError("No releases found for CISecurity/ControlsAssessmentSpecification")
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API returned {resp.status_code}")

    data = resp.json()
    assets = data.get("assets", [])
    if assets:
        zip_assets = [
            (asset["name"], asset["browser_download_url"])
            for asset in assets
            if asset["name"].endswith(".zip")
        ]
        if zip_assets:
            return zip_assets

    # No release assets — fall back to branch archive
    tag = data.get("tag_name", "main")
    archive_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/tags/{tag}.zip"
    return [(f"CIS-ControlsAssessmentSpecification-{tag}.zip", archive_url)]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "cis-controls"
    result = DownloadResult(framework="cis-controls")

    docs: list[tuple[str, str]]
    used_known = False
    try:
        docs = _fetch_release_archive()
    except RuntimeError as exc:
        result.notices.append(
            f"GitHub API unavailable ({exc}) — using main branch archive "
            f"(last verified {KNOWN_DOCS_VERIFIED})."
        )
        docs = KNOWN_DOCS
        used_known = True

    result.notices.append(
        "Content format is reStructuredText (.rst). "
        "The formatted CIS Controls v8 PDF requires a free CIS WorkBench account "
        f"and must be downloaded manually from {SOURCE_URL}."
    )

    if dry_run:
        for filename, _url in docs:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for filename, url in docs:
        target = dest / filename
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
