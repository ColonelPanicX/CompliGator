"""DoD Zero Trust and Cybersecurity Directives downloader.

All documents sourced from dowcio.war.gov/Library/ — direct PDF links,
no WAF restrictions, no CAC required. This replaces the previous
dodcio.defense.gov source, which returned 403 for all automated requests.

DoDI 8500.01 and DoDI 8510.01 remain manual_required — esd.whs.mil
returns 403 for automation and no public mirror has been identified.

Manual download sources:
  - DoDI 8500.01: https://www.esd.whs.mil/Directives/issuances/dodi/
  - DoDI 8510.01: https://www.esd.whs.mil/Directives/issuances/dodi/
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

# (filename, url) — documents that can be fetched automatically.
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "DoD-ZT-Strategy.pdf",
        BASE + "/Portals/0/Documents/Library/DoD-ZTStrategy.pdf",
    ),
    (
        "DoD-ZT-RA-v2.0.pdf",
        BASE + "/Portals/0/Documents/Library/(U)ZT_RA_v2.0(U)_Sep22.pdf",
    ),
    (
        "DoD-ZT-Capabilities-Activities.pdf",
        BASE + "/Portals/0/Documents/Library/ZT-CapabilitiesActivities.pdf",
    ),
    (
        "DoD-ZT-Capability-Execution-Roadmap-v1.1.pdf",
        BASE + "/Portals/0/Documents/Library/ZT-ExecutionRoadmap-v1.1.pdf",
    ),
    (
        "DoD-ZT-OT-Activities-Outcomes-v2.pdf",
        BASE + "/Portals/0/Documents/Library/ZT-OperationalTechnologyActivitiesOutcomes_v2.pdf",
    ),
    (
        "DoD-ZT-Strategy-Placemats.pdf",
        BASE + "/Portals/0/Documents/Library/ZT-StrategyPlacemats.pdf",
    ),
    (
        "DoD-ZT-PfMO-Newsletter-Nov2024.pdf",
        BASE + "/Portals/0/Documents/Library/ZT-NewsletterNov.pdf",
    ),
]

# Documents that require manual download — (filename, source_url).
MANUAL_DOCS: list[tuple[str, str]] = [
    (
        "DoDI-8500.01.pdf",
        "https://www.esd.whs.mil/Directives/issuances/dodi/",
    ),
    (
        "DoDI-8510.01.pdf",
        "https://www.esd.whs.mil/Directives/issuances/dodi/",
    ),
]


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "dod-zt"
    result = DownloadResult(framework="dod-zt")

    # Always surface the manual-required items regardless of dry_run.
    for filename, source in MANUAL_DOCS:
        result.manual_required.append((filename, source))

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
