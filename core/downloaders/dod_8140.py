"""DoD 8140 Cyberspace Workforce Management downloader.

Covers DoDD 8140.01, DoDI 8140.02, and DoDM 8140.03.
All documents sourced from dowcio.war.gov/Library/ — direct PDF links,
no WAF restrictions, no CAC required.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from core.state import StateFile

from .base import DownloadResult, download_file

SOURCE_URL = "https://dowcio.war.gov/Library/"

# Date these URLs were last manually verified.
KNOWN_DOCS_VERIFIED = "2026-03-31"

BASE = "https://dowcio.war.gov"

KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "DoDD-8140.01-Cyberspace-Workforce-Management.pdf",
        BASE + "/Portals/0/Documents/Library/DoDD-8140-01.pdf",
    ),
    (
        "DoDI-8140.02-Cyberspace-Workforce-Requirements.pdf",
        BASE + "/Portals/0/Documents/Library/DoDI-8140-02.pdf",
    ),
    (
        "DoDM-8140.03-Cyberspace-Workforce-Qualification.pdf",
        BASE + "/Portals/0/Documents/Library/DoDM-8140-03.pdf",
    ),
]


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "dod-8140"
    result = DownloadResult(framework="dod-8140")

    if dry_run:
        for filename, _url in KNOWN_DOCS:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for filename, url in KNOWN_DOCS:
        target = dest / filename
        ok, msg = download_file(session, url, target, force=force, state=state)
        if msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            result.errors.append((filename, msg))

    return result
