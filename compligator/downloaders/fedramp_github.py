"""FedRAMP automation artifacts downloader.

Downloads Rev 5 OSCAL content and guide documents from the GSA/fedramp-automation
GitHub repository:

  baselines/   — OSCAL profiles and resolved catalogs (HIGH/MODERATE/LOW/LI-SaaS)
  resources/   — FedRAMP extensions, threats, values, and information types
  templates/   — OSCAL templates (SSP, SAP, SAR, POAM)
  guides/      — OSCAL implementation guide PDFs

The GitHub API is used to discover file listings; actual downloads come from
raw.githubusercontent.com. Set the GITHUB_TOKEN environment variable to raise
the unauthenticated API rate limit from 60 to 5,000 requests/hour if needed.
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
)

SOURCE_URL = "https://github.com/GSA/fedramp-automation"
REPO_API_BASE = "https://api.github.com/repos/GSA/fedramp-automation/contents"

# NOTE: The GSA/fedramp-automation GitHub repository was removed (404 as of 2026-04-16).
# The FedRAMP OSCAL automation artifacts previously hosted there have not been
# relocated to a known public URL. These content sets are preserved for reference
# but will not resolve until a replacement source is identified.
#
# (GitHub API path, local subdir under dest, file extensions to include)
CONTENT_SETS: list[tuple[str, str, set[str]]] = [
    ("dist/content/rev5/baselines/json", "baselines", {".json"}),
    ("dist/content/rev5/resources/json", "resources", {".json"}),
    ("dist/content/rev5/templates/ssp/json", "templates", {".json"}),
    ("dist/content/rev5/templates/sap/json", "templates", {".json"}),
    ("dist/content/rev5/templates/sar/json", "templates", {".json"}),
    ("dist/content/rev5/templates/poam/json", "templates", {".json"}),
    ("documents/rev5", "guides", {".pdf"}),
]


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _api_headers() -> dict[str, str]:
    """Build request headers, including a GitHub token if set in the environment."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _list_files(api_path: str, include_ext: set[str]) -> list[tuple[str, str]]:
    """Return (filename, download_url) for matching files in a repo directory.

    Skips minified JSON variants (*-min.json) and subdirectories.
    Raises RuntimeError on API errors.
    """
    url = f"{REPO_API_BASE}/{api_path}"
    try:
        resp = requests.get(url, headers=_api_headers(), timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"GitHub API request failed for {api_path}: {exc}") from exc

    if resp.status_code == 403:
        raise RuntimeError(
            f"GitHub API rate-limited ({api_path}). "
            "Set GITHUB_TOKEN env var to increase the unauthenticated limit."
        )
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API returned {resp.status_code} for {api_path}")

    return [
        (item["name"], item["download_url"])
        for item in resp.json()
        if item["type"] == "file"
        and Path(item["name"]).suffix.lower() in include_ext
        and not item["name"].endswith("-min.json")
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    result = DownloadResult(framework="fedramp-github")
    # The GSA/fedramp-automation repo was removed as of 2026-04-16. All API
    # paths return 404. Return a notice rather than hammering the API with
    # 7 requests that will all fail.
    result.notices.append(
        "Source unavailable: GSA/fedramp-automation has been removed from GitHub. "
        "FedRAMP OSCAL artifacts have not been relocated to a known public URL. "
        "This framework cannot be synced until a replacement source is identified."
    )
    return result
