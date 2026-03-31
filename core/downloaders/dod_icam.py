"""DoD Identity, Credential, and Access Management (ICAM) downloader.

All documents sourced from dowcio.war.gov — direct PDF links,
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
        "DoD-Enterprise-ICAM-Reference-Design.pdf",
        BASE + "/Portals/0/Documents/Cyber/DoD_Enterprise_ICAM_Reference_Design.pdf",
    ),
    (
        "DoD-CIO-ICAM-Placemat.pdf",
        BASE + "/Portals/0/Documents/Cyber/DoD_CIO_ICAM_Placemat.pdf",
    ),
    (
        "DoD-ICAM-Workflow-Implementation-Guide.pdf",
        BASE + "/Portals/0/Documents/Library/ICAMWorkflowImplementationGuide.pdf",
    ),
    (
        "DoD-ICAM-Federation-Framework.pdf",
        BASE + "/Portals/0/Documents/Cyber/ICAM-FederationFramework.pdf",
    ),
    (
        "DoD-ICAM-Strategy.pdf",
        BASE + "/Portals/0/Documents/Cyber/ICAM_Strategy.pdf",
    ),
    (
        "DoD-ICAM-Memo-Accelerating-Adoption.pdf",
        BASE + "/Portals/0/Documents/Library/AcceleratingAdoptionICAM.pdf",
    ),
    (
        "DoD-ICAM-Memo-SAAR-Workflows.pdf",
        BASE + "/Portals/0/Documents/Library/CISOMemo-SAARICAMWorkflows.pdf",
    ),
]


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "dod-icam"
    result = DownloadResult(framework="dod-icam")

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
