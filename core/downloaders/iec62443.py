"""IEC 62443 Industrial Automation & Control Systems Security downloader (manual acquisition).

IEC 62443 is a multi-part standard series published by the International
Electrotechnical Commission (IEC). Parts are sold individually from the IEC
Webstore or national standards bodies (ANSI, BSI, etc.) and cannot be
downloaded automatically.

CompliGator maintains a directory structure and expected filename list so that:
  1. Users who have purchased these standards can drop them into source-content/iec62443/
  2. The normalizer will process them identically to any other PDF in the pipeline
  3. Sync status reflects which parts are present vs. missing

Place purchased PDFs in source-content/iec62443/ using the expected filenames below.

Source: https://www.iec.ch/cyber-security
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.state import StateFile

from .base import DownloadResult

SOURCE_URL = "https://www.iec.ch/cyber-security"

# (expected_filename, purchase_url, description)
# IEC 62443 series — organized by part number
MANUAL_DOCS: list[tuple[str, str, str]] = [
    # Part 1 — General
    (
        "IEC-62443-1-1-2009-Terminology-Concepts.pdf",
        "https://webstore.iec.ch/publication/7029",
        "IEC 62443-1-1:2009 — Terminology, Concepts and Models",
    ),
    (
        "IEC-62443-1-3-2013-System-Security-Compliance-Metrics.pdf",
        "https://webstore.iec.ch/publication/7031",
        "IEC 62443-1-3:2013 — System Security Compliance Metrics",
    ),
    (
        "IEC-62443-1-4-2018-IACS-Security-Lifecycle.pdf",
        "https://webstore.iec.ch/publication/62746",
        "IEC 62443-1-4:2018 — IACS Security Lifecycle and Use-Cases",
    ),
    # Part 2 — Policies & Procedures
    (
        "IEC-62443-2-1-2010-Security-Management-System.pdf",
        "https://webstore.iec.ch/publication/7032",
        "IEC 62443-2-1:2010 — Establishing an IACS Security Program",
    ),
    (
        "IEC-62443-2-2-2015-IACS-Security-Program-Ratings.pdf",
        "https://webstore.iec.ch/publication/21779",
        "IEC 62443-2-2:2015 — IACS Security Program Ratings",
    ),
    (
        "IEC-62443-2-3-2015-Patch-Management.pdf",
        "https://webstore.iec.ch/publication/21781",
        "IEC 62443-2-3:2015 — Patch Management in the IACS Environment",
    ),
    (
        "IEC-62443-2-4-2015-Service-Provider-Requirements.pdf",
        "https://webstore.iec.ch/publication/21802",
        "IEC 62443-2-4:2015 — Requirements for IACS Service Providers",
    ),
    # Part 3 — System
    (
        "IEC-62443-3-2-2020-Security-Risk-Assessment.pdf",
        "https://webstore.iec.ch/publication/61286",
        "IEC 62443-3-2:2020 — Security Risk Assessment for System Design",
    ),
    (
        "IEC-62443-3-3-2013-System-Security-Requirements.pdf",
        "https://webstore.iec.ch/publication/7033",
        "IEC 62443-3-3:2013 — System Security Requirements and Security Levels",
    ),
    # Part 4 — Component
    (
        "IEC-62443-4-1-2018-Secure-Product-Development.pdf",
        "https://webstore.iec.ch/publication/33615",
        "IEC 62443-4-1:2018 — Secure Product Development Lifecycle",
    ),
    (
        "IEC-62443-4-2-2019-Technical-Security-Requirements.pdf",
        "https://webstore.iec.ch/publication/34421",
        "IEC 62443-4-2:2019 — Technical Security Requirements for Components",
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
    result = DownloadResult(framework="iec62443")

    result.notices.append(
        "IEC 62443 parts require purchase from the IEC Webstore (webstore.iec.ch) "
        "or a national standards body. Place purchased PDFs in "
        "source-content/iec62443/ using the expected filenames listed below."
    )

    for filename, url, _desc in MANUAL_DOCS:
        result.manual_required.append((filename, url))

    return result
