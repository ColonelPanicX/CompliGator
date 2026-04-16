"""ISO/IEC 27000-series downloader (manual acquisition).

ISO/IEC standards are published by the International Organization for
Standardization (ISO) and require purchase from the ISO Store or a national
standards body (ANSI, BSI, DIN, etc.). Automated download is not possible.

CompliGator maintains a directory structure and expected filename list so that:
  1. Users who have purchased these standards can drop them into source-content/iso27k/
  2. The normalizer will process them identically to any other PDF in the pipeline
  3. Sync status reflects which standards are present vs. missing

Place purchased PDFs in source-content/iso27k/ using the expected filenames below.

Source: https://www.iso.org/isoiec-27001-information-security.html
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import DownloadResult

SOURCE_URL = "https://www.iso.org/isoiec-27001-information-security.html"

# (expected_filename, purchase_url, description)
MANUAL_DOCS: list[tuple[str, str, str]] = [
    (
        "ISO-IEC-27001-2022-Information-Security-Management-Systems.pdf",
        "https://www.iso.org/standard/27001",
        "ISO/IEC 27001:2022 — ISMS Requirements",
    ),
    (
        "ISO-IEC-27002-2022-Information-Security-Controls.pdf",
        "https://www.iso.org/standard/75652.html",
        "ISO/IEC 27002:2022 — Information Security Controls",
    ),
    (
        "ISO-IEC-27005-2022-Information-Security-Risk-Management.pdf",
        "https://www.iso.org/standard/80585.html",
        "ISO/IEC 27005:2022 — Information Security Risk Management",
    ),
    (
        "ISO-IEC-27017-2015-Cloud-Security-Controls.pdf",
        "https://www.iso.org/standard/43757.html",
        "ISO/IEC 27017:2015 — Cloud Service Security Controls",
    ),
    (
        "ISO-IEC-27018-2019-PII-Cloud.pdf",
        "https://www.iso.org/standard/76559.html",
        "ISO/IEC 27018:2019 — Protection of PII in Public Clouds",
    ),
    (
        "ISO-IEC-27701-2019-Privacy-Information-Management.pdf",
        "https://www.iso.org/standard/71670.html",
        "ISO/IEC 27701:2019 — Privacy Information Management System",
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
    result = DownloadResult(framework="iso27k")

    result.notices.append(
        "ISO/IEC 27000-series standards require purchase from the ISO Store "
        "(iso.org) or a national standards body. Place purchased PDFs in "
        "source-content/iso27k/ using the expected filenames listed below."
    )

    for filename, url, _desc in MANUAL_DOCS:
        result.manual_required.append((filename, url))

    return result
