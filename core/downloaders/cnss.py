"""CNSS Instructions & Policies downloader.

Downloads key CNSS instructions from public mirrors. cnss.gov requires a DoD
root certificate for direct access and is not reachable by standard automation.
All documents are sourced from publicly accessible government mirrors (dni.gov,
rmf.org, etc.) and clearly identified as such.

Covered documents:
  - CNSSI 1253  Security Categorization and Control Selection for NSS
  - CNSSI 4009  Committee on National Security Systems Glossary
  - CNSSI 4011  Information Assurance Training (if mirror available)
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

SOURCE_URL = "https://www.cnss.gov/CNSS/issuances/Instructions.cfm"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-03"

# Curated list of CNSS documents from public mirrors.
# cnss.gov requires DoD root certificate; these are publicly accessible equivalents.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "CNSSI-1253-Security-Categorization-Control-Selection.pdf",
        "https://www.dni.gov/files/NCSC/documents/nittf/CNSSI_No1253.pdf",
    ),
    (
        "CNSSI-4009-National-Information-Assurance-Glossary.pdf",
        "https://rmf.org/wp-content/uploads/2017/10/CNSSI-4009.pdf",
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
    dest = output_dir / "cnss"
    result = DownloadResult(framework="cnss")

    result.notices.append(
        f"cnss.gov requires a DoD root certificate and is not directly accessible. "
        f"Documents sourced from public government mirrors (last verified {KNOWN_DOCS_VERIFIED}). "
        f"Authoritative source: {SOURCE_URL}"
    )

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
