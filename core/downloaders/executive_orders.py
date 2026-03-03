"""Cybersecurity Executive Orders downloader.

Downloads PDF text of cybersecurity-relevant Executive Orders from the
Federal Register. Uses the Federal Register JSON API to discover the PDF
URL for each known document number, with a direct-URL fallback.

Curated EO list (document numbers from federalregister.gov):
  - EO 14028 — Improving the Nation's Cybersecurity (May 2021)
  - EO 14144 — Strengthening and Promoting Innovation in the Nation's
               Cybersecurity (January 2025)

Note: Additional EOs (e.g., sustaining select EO 14144 provisions, expected
June 2025) should be added here when their Federal Register document numbers
are confirmed.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from core.state import StateFile

from .base import (
    REQUEST_TIMEOUT,
    USER_AGENT,
    DownloadResult,
    download_file,
)

FR_API_BASE = "https://www.federalregister.gov/api/v1/documents"
FR_PDF_BASE = "https://www.federalregister.gov/documents/full_text/pdf"

# (doc_number, short_label, output_filename)
KNOWN_EOS: list[tuple[str, str, str]] = [
    (
        "2021-10460",
        "EO 14028 — Improving the Nation's Cybersecurity",
        "EO-14028-Improving-Nations-Cybersecurity.pdf",
    ),
    (
        "2025-01470",
        "EO 14144 — Strengthening and Promoting Innovation in the Nation's Cybersecurity",
        "EO-14144-Strengthening-Nations-Cybersecurity.pdf",
    ),
]


# ---------------------------------------------------------------------------
# Federal Register API helpers
# ---------------------------------------------------------------------------


def _get_pdf_url(doc_number: str) -> str:
    """Resolve the PDF URL for a Federal Register document number.

    Falls back to the known URL pattern if the API is unavailable.
    """
    api_url = f"{FR_API_BASE}/{doc_number}.json"
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            pdf_url = data.get("pdf_url") or data.get("full_text_xml_url")
            if pdf_url and pdf_url.endswith(".pdf"):
                return pdf_url
    except requests.RequestException:
        pass

    # Fallback: construct direct PDF URL from known FR pattern
    return f"{FR_PDF_BASE}/{doc_number}.pdf"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    output_dir: Path,
    dry_run: bool = False,
    force: bool = False,
    state: Optional["StateFile"] = None,
) -> DownloadResult:
    dest = output_dir / "executive-orders"
    result = DownloadResult(framework="executive-orders")

    # Resolve PDF URLs for each known EO
    docs: list[tuple[str, str]] = []
    for doc_number, label, filename in KNOWN_EOS:
        try:
            pdf_url = _get_pdf_url(doc_number)
            docs.append((filename, pdf_url))
        except Exception as exc:  # noqa: BLE001
            result.errors.append((filename, f"Could not resolve URL for {label}: {exc}"))

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
            result.errors.append((filename, f"{msg} ({url})"))

    return result
