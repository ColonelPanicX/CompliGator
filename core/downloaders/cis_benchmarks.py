"""CIS Benchmarks downloader (manual acquisition — login required).

CIS Benchmarks are freely available from the CIS WorkBench portal at
workbench.cisecurity.org, but require a free account to download. There are
100+ benchmarks covering operating systems, cloud platforms, containers,
network devices, and applications — with version numbers that update
frequently.

CompliGator uses a directory-scan model for this framework:
  - source-content/cis-benchmarks/ is the target directory
  - Any PDF placed there is auto-adopted on the next sync
  - No fixed filename list is enforced (filenames vary by benchmark and version)

To populate: create a free account at https://workbench.cisecurity.org,
download whichever benchmarks are relevant to your environment, and place
the PDFs in source-content/cis-benchmarks/.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.state import StateFile

from .base import DownloadResult

SOURCE_URL = "https://workbench.cisecurity.org/benchmarks"

NOTICE = (
    "CIS Benchmarks require a free CIS WorkBench account. "
    "Download from workbench.cisecurity.org and place PDFs in "
    "source-content/cis-benchmarks/. Any filename is accepted — "
    "files are auto-adopted on next sync."
)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    result = DownloadResult(framework="cis-benchmarks")
    dest_dir = output_dir / "cis-benchmarks"
    dest_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(dest_dir.glob("*.pdf"))

    if pdfs:
        for pdf in pdfs:
            if state is not None and state.needs_adopt(pdf):
                state.adopt(pdf, SOURCE_URL)
            result.skipped.append(pdf.name)
    else:
        result.notices.append(NOTICE)

    return result
