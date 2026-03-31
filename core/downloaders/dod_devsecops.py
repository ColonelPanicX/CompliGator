"""DoD DevSecOps and Continuous ATO (cATO) downloader.

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
        "DoD-DevSecOps-Fundamentals-v2.5.pdf",
        BASE + "/Portals/0/Documents/Library/DoD Enterprise DevSecOps Fundamentals v2.5.pdf",
    ),
    (
        "DoD-DevSecOps-Activities-Tools-Guidebook.pdf",
        BASE + "/Portals/0/Documents/Library/DevSecOpsActivitesToolsGuidebook.pdf",
    ),
    (
        "DoD-DevSecOps-Playbook.pdf",
        BASE + "/Portals/0/Documents/Library/DevSecOps Playbook_DoD-CIO_20211019.pdf",
    ),
    (
        "DoD-State-of-DevSecOps-Report.pdf",
        BASE + "/Portals/0/Documents/Library/DevSecOpsStateOf.pdf",
    ),
    (
        "DoD-DevSecOps-Reference-Design-CNCF-Kubernetes.pdf",
        BASE + "/Portals/0/Documents/Library/"
        "DoD Enterprise DevSecOps Reference Design - CNCF Kubernetes w-DD1910_cleared_20211022.pdf",
    ),
    (
        "DoD-DevSecOps-Reference-Design-CNCF-Multi-Cluster-Kubernetes.pdf",
        BASE + "/Portals/0/Documents/Library/DoDReferenceDesign-CNCFMulti-ClusterKubernetes.pdf",
    ),
    (
        "DoD-cATO-Memo-20220204.pdf",
        BASE + "/Portals/0/Documents/Library/20220204-cATO-memo.PDF",
    ),
    (
        "DoD-cATO-Memo-Signed-Cleared.pdf",
        BASE + "/Portals/0/Documents/Library/20220204-cATO-memo-Signed-Cleared.pdf",
    ),
    (
        "DoD-cATO-Evaluation-Criteria.pdf",
        BASE + "/Portals/0/Documents/Library/cATO-EvaluationCriteria.pdf",
    ),
    (
        "DoD-Continuous-Authorization-Implementation-Guide.pdf",
        BASE + "/Portals/0/Documents/Library/DoDCIO-ContinuousAuthorizationImplementationGuide.pdf",
    ),
]


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "dod-devsecops"
    result = DownloadResult(framework="dod-devsecops")

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
