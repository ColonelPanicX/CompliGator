"""DCSA NISPOM (32 CFR Part 117) downloader.

Downloads the National Industrial Security Program Operating Manual regulatory
text from eCFR as a single HTML page. The NISPOM was codified as 32 CFR Part
117 in February 2021 and is the primary regulatory framework for facility
clearances (FCL) for cleared DoD contractors.

Note: eCFR serves 32 CFR Part 117 only as a full-part page; subpart-level
URLs redirect to a bot-detection page and cannot be downloaded directly.

Supplemental DCSA guidance PDFs (dcsa.mil) require authentication/browser
interaction and are surfaced as manual_required.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from core.state import StateFile

from .base import (
    DownloadResult,
    download_file,
)

SOURCE_URL = "https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-M/part-117"

# eCFR HTML page — full Part 117 (all subparts included).
# Subpart-level URLs redirect to a bot-detection page and cannot be downloaded.
# (filename, url)
ECFR_PAGES: list[tuple[str, str]] = [
    (
        "NISPOM-32-CFR-Part-117-Full.html",
        "https://www.ecfr.gov/current/title-32/subtitle-A/chapter-I/subchapter-M/part-117",
    ),
]

# dcsa.mil supplemental guidance PDFs — require browser interaction (403 for automation).
MANUAL_DOCS: list[tuple[str, str]] = [
    (
        "DCSA-NISPOM-Guidance-Supplemental.pdf",
        "https://www.dcsa.mil/is/nispom/",
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
    dest = output_dir / "nispom"
    result = DownloadResult(framework="nispom")

    for filename, url in MANUAL_DOCS:
        result.manual_required.append((filename, url))

    if dry_run:
        for filename, _url in ECFR_PAGES:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for filename, url in ECFR_PAGES:
        target = dest / filename
        ok, msg = download_file(
            session, url, target, force=force, referer=SOURCE_URL, state=state
        )
        if msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            result.errors.append((filename, msg))

    return result
