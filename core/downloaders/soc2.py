"""SOC 2 / AICPA Trust Services Criteria downloader.

The AICPA Trust Services Criteria (TSC) is the framework underlying SOC 2
attestation reports. It covers five trust service categories: Security,
Availability, Processing Integrity, Confidentiality, and Privacy.

The TSC 2017 document (with subsequent revisions) is freely downloadable from
aicpa-cima.com without an account or license agreement.

Source: https://www.aicpa-cima.com/resources/landing/trust-services-criteria
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from core.state import StateFile

from .base import DownloadResult, download_file

SOURCE_URL = "https://www.aicpa-cima.com/resources/landing/trust-services-criteria"

KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "AICPA-Trust-Services-Criteria-2017.pdf",
        "https://www.aicpa-cima.com/content/dam/aicpa/interestareas/frc/assuranceadvisoryservices/downloadabledocuments/trust-services-criteria.pdf",
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
    result = DownloadResult(framework="soc2")
    dest_dir = output_dir / "soc2"
    session = requests.Session()

    for filename, url in KNOWN_DOCS:
        dest = dest_dir / filename

        if dry_run:
            if state is not None and state.is_fresh(dest, url):
                result.skipped.append(filename)
            elif dest.exists() and dest.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
            continue

        ok, msg = download_file(session, url, dest, force=force, state=state)
        if ok and msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            result.errors.append((filename, msg, url))

    return result
