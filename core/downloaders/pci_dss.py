"""PCI DSS v4.0.1 downloader.

Downloads PCI DSS v4.0.1 documents from the PCI Security Standards Council.

SAQs and supplemental documents are available as direct downloads from the
PCI SSC document listing CDN (listings.pcisecuritystandards.org). The main
PCI DSS standard requires accepting a license agreement via the PCI SSC portal
and is surfaced as manual_required.

SAQ coverage:
  - SAQ A        — Card-not-present, all cardholder data functions outsourced
  - SAQ B        — Imprint-only or standalone dial-out terminal merchants
  - SAQ B-IP     — Standalone IP-connected PTS POI terminals
  - SAQ C        — Payment app systems connected to the internet
  - SAQ C-VT     — Web-based virtual payment terminals
  - SAQ D-Merch  — All other SAQ-eligible merchants
  - SAQ D-SP     — SAQ-eligible service providers
  - Summary of Changes
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

SOURCE_URL = "https://www.pcisecuritystandards.org/document_library/"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-03"

# SAQ and supplemental documents — direct CDN downloads, no click-through required.
# (filename, url)
# Note: URL structure verified against PCI SSC CDN patterns; confirm during UAT.
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "PCI-DSS-v4-0-1-SAQ-A.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-A.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-SAQ-B.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-B.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-SAQ-B-IP.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-B-IP.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-SAQ-C.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-C.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-SAQ-C-VT.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-C-VT.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-SAQ-D-Merchant.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-D-Merchant.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-SAQ-D-SP.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-SAQ-D-SP.pdf",
    ),
    (
        "PCI-DSS-v4-0-1-Summary-of-Changes.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-1-Summary-of-Changes-r1.pdf",
    ),
]

# Main standard requires accepting a license agreement via the PCI SSC portal.
MANUAL_DOCS: list[tuple[str, str]] = [
    (
        "PCI-DSS-v4-0-1.pdf",
        "https://www.pcisecuritystandards.org/document_library/",
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
    dest = output_dir / "pci-dss"
    result = DownloadResult(framework="pci-dss")

    # Main standard requires portal click-through — surface as manual
    for filename, url in MANUAL_DOCS:
        result.manual_required.append((filename, url))

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
