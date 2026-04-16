"""FTC Safeguards Rule (16 CFR Part 314) downloader.

Downloads:
  - FTC Safeguards Rule final rule PDF from ftc.gov
  - Current regulatory text (16 CFR Part 314) as HTML from eCFR

The Safeguards Rule (Gramm-Leach-Bliley Act, 16 CFR Part 314) governs
information security programs for non-bank financial institutions. The 2023
amendment expanded coverage to mortgage brokers, payday lenders, and other
non-bank entities. Required reading for fintech/financial services CSPs.
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

SOURCE_URL = "https://www.ftc.gov/legal-library/browse/rules/safeguards-rule"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-03"

# eCFR HTML pages to download (title, filename, url)
ECFR_PAGES: list[tuple[str, str]] = [
    (
        "FTC-Safeguards-Rule-16-CFR-Part-314.html",
        "https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-314",
    ),
]

# Curated fallback — used if scraping ftc.gov fails.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
    (
        "FTC-Safeguards-Rule-Final-Rule-2023.pdf",
        "https://www.ftc.gov/system/files/ftc_gov/pdf/r14152-safeguards-rule-nprm-2021.pdf",
    ),
]


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------


def _scrape_pdfs() -> list[tuple[str, str]]:
    """Scrape ftc.gov/legal-library/browse/rules/safeguards-rule for PDF links.

    Raises RuntimeError on failure.
    """
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(SOURCE_URL, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")
    docs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        full_url = urljoin(SOURCE_URL, href)
        if Path(urlparse(full_url).path).suffix.lower() != ".pdf":
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        filename = Path(urlparse(full_url).path).name or "ftc-safeguards.pdf"
        docs.append((filename, full_url))

    if not docs:
        raise RuntimeError("No PDF links found on FTC safeguards rule page")
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
    dest = output_dir / "ftc-safeguards"
    result = DownloadResult(framework="ftc-safeguards")

    # Build combined doc list: scraped PDFs (or fallback) + eCFR HTML pages
    pdf_docs: list[tuple[str, str]]
    used_known = False
    try:
        pdf_docs = _scrape_pdfs()
    except RuntimeError as exc:
        result.notices.append(
            f"Scrape failed ({exc}) — using curated fallback list "
            f"(last verified {KNOWN_DOCS_VERIFIED})."
        )
        pdf_docs = KNOWN_DOCS
        used_known = True

    all_docs = pdf_docs + ECFR_PAGES

    if dry_run:
        for filename, _url in all_docs:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)
    session = requests.Session()

    for filename, url in all_docs:
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
