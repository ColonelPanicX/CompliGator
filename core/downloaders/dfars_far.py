"""DFARS / FAR Cybersecurity Clauses downloader.

Downloads the HTML text of key DFARS and FAR cybersecurity contract clauses
from the Electronic Code of Federal Regulations (eCFR) at ecfr.gov.

Covered clauses:
  DFARS (Title 48, Chapter 2, Part 252):
    - 252.204-7012  Safeguarding Covered Defense Information and Cyber Incident Reporting
    - 252.204-7019  Notice of NIST SP 800-171 DoD Assessment Requirements
    - 252.204-7020  NIST SP 800-171 DoD Assessment Requirements
    - 252.204-7021  Cybersecurity Maturity Model Certification Requirements

  FAR (Title 48, Chapter 1, Part 52):
    - 52.239-1  Privacy or Security Safeguards

Saved as .html files for downstream normalization.
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

SOURCE_URL = "https://www.ecfr.gov"

# (filename, ecfr_url)
CLAUSES: list[tuple[str, str]] = [
    (
        "DFARS-252.204-7012-Safeguarding-Covered-Defense-Information.html",
        "https://www.ecfr.gov/current/title-48/chapter-2/subchapter-H/part-252/subpart-B/section-252.204-7012",
    ),
    (
        "DFARS-252.204-7019-Notice-NIST-800-171-Assessment-Requirements.html",
        "https://www.ecfr.gov/current/title-48/chapter-2/subchapter-H/part-252/subpart-B/section-252.204-7019",
    ),
    (
        "DFARS-252.204-7020-NIST-800-171-Assessment-Requirements.html",
        "https://www.ecfr.gov/current/title-48/chapter-2/subchapter-H/part-252/subpart-B/section-252.204-7020",
    ),
    (
        "DFARS-252.204-7021-CMMC-Requirements.html",
        "https://www.ecfr.gov/current/title-48/chapter-2/subchapter-H/part-252/subpart-B/section-252.204-7021",
    ),
    (
        "FAR-52.239-1-Privacy-or-Security-Safeguards.html",
        "https://www.ecfr.gov/current/title-48/chapter-1/subchapter-H/part-52/subpart-52.2/section-52.239-1",
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
    dest = output_dir / "dfars-far"
    result = DownloadResult(framework="dfars-far")

    if dry_run:
        for filename, _url in CLAUSES:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for filename, url in CLAUSES:
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
