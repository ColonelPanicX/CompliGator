"""CSA Cloud Controls Matrix (CCM) v4.1 downloader.

Downloads the CCM v4.1 XLSX (primary control set), PDF, and implementation
guidelines from the Cloud Security Alliance.

Approach: try the CSA direct download URL first, fall back to KNOWN_DOCS.
CSA resources are publicly accessible without account registration via the
/download/artifacts/ path.
"""

from __future__ import annotations

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

SOURCE_URL = "https://cloudsecurityalliance.org/artifacts/cloud-controls-matrix-v4-1"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-02"

# Curated fallback — used if live discovery fails.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "CSA-CCM-v4.1.xlsx",
        "https://cloudsecurityalliance.org/download/artifacts/cloud-controls-matrix-v4-1",
    ),
]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _fetch_docs() -> list[tuple[str, str]]:
    """Try to resolve the CSA CCM v4.1 artifact download URL.

    CSA's /download/artifacts/ path performs a redirect to the actual file.
    Returns [(filename, resolved_url)] on success, raises RuntimeError on failure.
    """
    headers = {"User-Agent": USER_AGENT}
    url = "https://cloudsecurityalliance.org/download/artifacts/cloud-controls-matrix-v4-1"
    try:
        resp = requests.head(url, headers=headers, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if resp.status_code not in (200, 302):
        raise RuntimeError(f"HTTP {resp.status_code} from CSA download endpoint")

    final_url = resp.url
    filename = Path(final_url).name
    ext = Path(filename).suffix.lower()

    if ext not in {".xlsx", ".pdf", ".zip"}:
        raise RuntimeError(f"Resolved URL does not appear to be a file: {final_url}")

    return [(filename or "CSA-CCM-v4.1.xlsx", final_url)]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "csa-ccm"
    result = DownloadResult(framework="csa-ccm")

    docs: list[tuple[str, str]]
    used_known = False
    try:
        docs = _fetch_docs()
    except RuntimeError as exc:
        result.notices.append(
            f"Live discovery failed ({exc}) — using curated fallback list "
            f"(last verified {KNOWN_DOCS_VERIFIED})."
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
