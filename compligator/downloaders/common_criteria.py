"""Common Criteria (ISO/IEC 15408) downloader.

The Common Criteria for Information Technology Security Evaluation (CC) is
published by the Common Criteria Recognition Arrangement (CCRA) and freely
available from the Common Criteria Portal at commoncriteriaportal.org.

This downloader retrieves the core CC v3.1 Revision 5 documents:
  - Part 1: Introduction and General Model
  - Part 2: Security Functional Components
  - Part 3: Security Assurance Components
  - CEM: Common Evaluation Methodology

These are the normative documents that define the CC evaluation framework used
by NIAP (US), ANSSI (France), BSI (Germany), CESG (UK), and other national
schemes under the CCRA mutual recognition agreement.

Source: https://www.commoncriteriaportal.org/cc/
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import DownloadResult, download_file

SOURCE_URL = "https://www.commoncriteriaportal.org/cc/"

# CC v3.1 Revision 5 — freely available from the CC Portal
# (local_filename, download_url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "CC-v3.1-Rev5-Part1-Introduction-and-General-Model.pdf",
        "https://www.commoncriteriaportal.org/files/ccfiles/CCPART1V3.1R5.pdf",
    ),
    (
        "CC-v3.1-Rev5-Part2-Security-Functional-Components.pdf",
        "https://www.commoncriteriaportal.org/files/ccfiles/CCPART2V3.1R5.pdf",
    ),
    (
        "CC-v3.1-Rev5-Part3-Security-Assurance-Components.pdf",
        "https://www.commoncriteriaportal.org/files/ccfiles/CCPART3V3.1R5.pdf",
    ),
    (
        "CC-v3.1-Rev5-CEM-Common-Evaluation-Methodology.pdf",
        "https://www.commoncriteriaportal.org/files/ccfiles/CEMV3.1R5.pdf",
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
    result = DownloadResult(framework="common-criteria")
    dest_dir = output_dir / "common-criteria"
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
