"""NIST Privacy Framework v1.0 downloader.

The NIST Privacy Framework: A Tool for Improving Privacy through Enterprise
Risk Management (Version 1.0) is published at nist.gov/privacy-framework.

It is a companion to the NIST Cybersecurity Framework and is not part of the
SP 800-series — it is a CSWP publication hosted outside the CSRC catalog, so
it is not captured by the NIST finals/drafts dynamic crawl.

Source: https://www.nist.gov/privacy-framework
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from core.state import StateFile

from .base import DownloadResult, download_file

SOURCE_URL = "https://www.nist.gov/privacy-framework"

KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "NIST-Privacy-Framework-v1.0.pdf",
        "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.01162020.pdf",
    ),
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
    result = DownloadResult(framework="nist-privacy")
    dest_dir = output_dir / "nist-privacy"
    session = requests.Session()

    for filename, url in KNOWN_DOCS:
        dest = dest_dir / filename

        if dry_run:
            if state is not None and state.is_fresh(dest, url):
                result.skipped.append(filename)
            elif dest.exists() and dest.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
            continue

        ok, msg = download_file(session, url, dest, force=force, state=state)
        if ok and msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            result.errors.append((filename, msg, url))

    return result
