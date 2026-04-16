"""GovRAMP (formerly StateRAMP) downloader.

Downloads public documents from govramp.org/documents/: Security Assessment
Framework, Core Controls, and supplemental XLSX/PDF resources.

GovRAMP formally rebranded from StateRAMP in February 2025. Any existing
StateRAMP placeholder directories should be considered superseded by the
govramp/ output directory.

Approach: scrape govramp.org/documents/ for PDF/XLSX links (direct CDN URLs),
fall back to KNOWN_DOCS if scraping fails. ZIP packages (3PAO, SP) are
intentionally excluded — they are assessment templates rather than policy docs.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from compligator.state import StateFile

from .base import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    DownloadResult,
    download_file,
)

SOURCE_URL = "https://www.govramp.org/documents/"

# File extensions to download (skip ZIPs — large assessment template packages)
DOWNLOAD_EXTENSIONS = {".pdf", ".xlsx"}

# Date the KNOWN_DOCS list was last manually verified against govramp.org
KNOWN_DOCS_VERIFIED = "2026-03-02"

# Curated fallback — used if scraping fails.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "GovRAMP-Security-Assessment-Framework-4.1.pdf",
        "https://s33104.pcdn.co/wp-content/uploads/2025/09/GovRAMP-Security-Assessment-Framework-4.1-Adopted-9-2025.pdf",
    ),
    (
        "GovRAMP-Core-Controls.xlsx",
        "https://s33104.pcdn.co/wp-content/uploads/2025/05/GovRAMP-Core-Controls.xlsx",
    ),
    (
        "GovRAMP-Data-Classification-Tool.pdf",
        "https://s33104.pcdn.co/wp-content/uploads/2025/01/Data-Classification-Tool.pdf",
    ),
    (
        "GovRAMP-CJIS-6.0-Aligned-Overlay.xlsx",
        "https://s33104.pcdn.co/wp-content/uploads/2026/01/GovRAMP-CJIS-6.0-Aligned-Overlay-Control-and-Parameters.xlsx",
    ),
    (
        "GovRAMP-Annual-Assessment-Controls-Selection-Workbook.xlsx",
        "https://s33104.pcdn.co/wp-content/uploads/2025/02/StateRAMP-Authorization-Annual-Assessment-Controls-Selection-Workbook.xlsx",
    ),
]


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------


def _scrape_documents() -> list[tuple[str, str]]:
    """Return (filename, url) pairs scraped from govramp.org/documents/.

    Raises RuntimeError on request or parse failure.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(SOURCE_URL, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} from {SOURCE_URL}")

    soup = BeautifulSoup(resp.text, "html.parser")
    docs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        full_url = urljoin(SOURCE_URL, href)
        ext = Path(urlparse(full_url).path).suffix.lower()
        if ext not in DOWNLOAD_EXTENSIONS:
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        filename = Path(urlparse(full_url).path).name or "unknown"
        docs.append((filename, full_url))

    if not docs:
        raise RuntimeError("No PDF/XLSX links found on documents page")

    return docs


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "govramp"
    result = DownloadResult(framework="govramp")

    docs: list[tuple[str, str]]
    used_known = False
    try:
        docs = _scrape_documents()
    except RuntimeError as exc:
        result.notices.append(
            f"Scrape failed ({exc}) — using curated fallback list "
            f"(last verified {KNOWN_DOCS_VERIFIED})."
        )
        docs = KNOWN_DOCS
        used_known = True

    if dry_run:
        for filename, _url in docs:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for filename, url in docs:
        target = dest / filename
        ok, msg = download_file(session, url, target, force=force, state=state)
        if msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            if used_known:
                result.errors.append((filename, msg))
            else:
                result.errors.append((filename, f"{msg} ({url})"))

    return result
