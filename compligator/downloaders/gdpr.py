"""GDPR (General Data Protection Regulation) downloader.

Regulation (EU) 2016/679 of the European Parliament and of the Council
(General Data Protection Regulation). The full regulation text is freely
available from EUR-Lex, the European Union's official law publication system.

Source: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import DownloadResult, download_file

SOURCE_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"

KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "GDPR-Regulation-EU-2016-679.pdf",
        "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32016R0679",
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
    result = DownloadResult(framework="gdpr")
    dest_dir = output_dir / "gdpr"
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
