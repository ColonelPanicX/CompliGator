"""PCI DSS downloader.

Downloads PCI DSS SAQ documents from the PCI Security Standards Council.

PCI DSS v4.0 SAQs are available as direct downloads from the PCI SSC CDN
(listings.pcisecuritystandards.org). PCI DSS v4.0.1 SAQs and the main
standard require accepting a license agreement via the PCI SSC portal and
are surfaced as manual_required.

Note: v4.0 and v4.0.1 SAQs differ only in minor editorial clarifications.

SAQ coverage (v4.0 from official CDN):
  - SAQ A               — Card-not-present, all cardholder data functions outsourced
  - SAQ B               — Imprint-only or standalone dial-out terminal merchants
  - SAQ B-IP            — Standalone IP-connected PTS POI terminals
  - SAQ C               — Payment app systems connected to the internet
  - SAQ C-VT            — Web-based virtual payment terminals
  - SAQ D-Merchant      — All other SAQ-eligible merchants
  - SAQ D-Service-Provider — SAQ-eligible service providers
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import (
    DownloadResult,
    download_file,
)

SOURCE_URL = "https://www.pcisecuritystandards.org/document_library/"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-03"

# PCI DSS v4.0 SAQs — direct CDN downloads from the official PCI SSC CDN.
# v4.0.1 SAQs are not available on the CDN; v4.0 and v4.0.1 differ only in
# minor editorial clarifications.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "PCI-DSS-v4-0-SAQ-A.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-A.pdf",
    ),
    (
        "PCI-DSS-v4-0-SAQ-B.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-B.pdf",
    ),
    (
        "PCI-DSS-v4-0-SAQ-B-IP.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-B-IP.pdf",
    ),
    (
        "PCI-DSS-v4-0-SAQ-C.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-C.pdf",
    ),
    (
        "PCI-DSS-v4-0-SAQ-C-VT.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-C-VT.pdf",
    ),
    (
        "PCI-DSS-v4-0-SAQ-D-Merchant.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-D-Merchant.pdf",
    ),
    (
        "PCI-DSS-v4-0-SAQ-D-Service-Provider.pdf",
        "https://listings.pcisecuritystandards.org/documents/PCI-DSS-v4-0-SAQ-D-Service-Provider.pdf",
    ),
]

# Main standard and v4.0.1 SAQs require accepting a license agreement via the PCI SSC portal.
MANUAL_DOCS: list[tuple[str, str]] = [
    (
        "PCI-DSS-v4-0-1.pdf",
        "https://www.pcisecuritystandards.org/document_library/",
    ),
    (
        "PCI-DSS-v4-0-1-SAQs.pdf",
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
