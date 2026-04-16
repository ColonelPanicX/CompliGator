"""DoD Cloud Security downloader.

Covers the DoD Cloud Security Playbook series, FinOps Strategy, and CNAP Reference Design.
All documents sourced from dowcio.war.gov/Library/ — direct PDF links,
no WAF restrictions, no CAC required.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import DownloadResult, download_file

SOURCE_URL = "https://dowcio.war.gov/Library/"

# Date these URLs were last manually verified.
KNOWN_DOCS_VERIFIED = "2026-03-31"

BASE = "https://dowcio.war.gov"

KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "DoD-Cloud-Security-Playbook-Overview.pdf",
        BASE + "/Portals/0/Documents/Library/CloudSecurityPlaybookOverview.pdf",
    ),
    (
        "DoD-Cloud-Security-Playbook-Vol1.pdf",
        BASE + "/Portals/0/Documents/Library/CloudSecurityPlaybookVol1.pdf",
    ),
    (
        "DoD-Cloud-Security-Playbook-Vol2.pdf",
        BASE + "/Portals/0/Documents/Library/CloudSecurityPlaybookVol2.pdf",
    ),
    (
        "DoD-Cloud-FinOps-Strategy.pdf",
        BASE + "/Portals/0/Documents/Library/DoDCloudFinOpsStrategy.pdf",
    ),
    (
        "DoD-CNAP-Reference-Design-v1.0.pdf",
        BASE + "/Portals/0/Documents/Library/CNAP_RefDesign_v1.0.pdf",
    ),
]


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "dod-cloud"
    result = DownloadResult(framework="dod-cloud")

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
