"""NSA Cybersecurity Advisories & Guidance downloader.

NSA publishes advisories and guidance documents at media.defense.gov.
That CDN consistently returns HTTP 403 for all automated access — plain
requests, Playwright headless (attachment mode), Playwright navigate, and
Playwright navigate with Referer header all fail identically.

All documents are therefore surfaced as manual_required with their direct
URLs so users can download them from a browser and place them in the output
directory.

The nsa.gov/Cybersecurity/Advisories page is JavaScript-rendered and not
reliably scrapeable; the nsacyber GitHub org does not maintain a consolidated
publications release.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.state import StateFile

from .base import DownloadResult

SOURCE_URL = "https://www.nsa.gov/Press-Room/Cybersecurity-Advisories-Guidance/"

# Curated list of key NSA cybersecurity advisory PDFs.
# All are on media.defense.gov which blocks automated access (HTTP 403).
# (filename, url)
MANUAL_DOCS: list[tuple[str, str]] = [
    (
        "NSA-CISA-Top10-Cybersecurity-Misconfigurations.pdf",
        "https://media.defense.gov/2023/Oct/05/2003314578/-1/-1/0/NSA-CISA-Top10-Network-Misconfigurations.PDF",
    ),
    (
        "NSA-Kubernetes-Hardening-Guide-v1.2.pdf",
        "https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF",
    ),
    (
        "NSA-CISA-Network-Infrastructure-Security-Guide.pdf",
        "https://media.defense.gov/2023/Mar/21/2003183949/-1/-1/0/CSI_NSA-CISA-FBI-MS-ISAC_SCA_NETWORK_INFRASTRUCTURE_SECURITY_GUIDE.PDF",
    ),
    (
        "NSA-Zero-Trust-Pillar-User-Maturity-Guide.pdf",
        "https://media.defense.gov/2023/Apr/05/2003198140/-1/-1/0/CSITM_ZT_USER_PILLAR_MATURITY_GUIDE.PDF",
    ),
    (
        "NSA-Zero-Trust-Pillar-Device-Maturity-Guide.pdf",
        "https://media.defense.gov/2023/Apr/05/2003198138/-1/-1/0/CSITM_ZT_DEVICE_PILLAR_MATURITY_GUIDE.PDF",
    ),
    (
        "NSA-Enduring-Security-Framework-Identity-Credential-Access-Management.pdf",
        "https://media.defense.gov/2023/Mar/21/2003183948/-1/-1/0/ESF_IDENTITY_CREDENTIAL_ACCESS_MANAGEMENT.PDF",
    ),
    (
        "NSA-Software-Memory-Safety.pdf",
        "https://media.defense.gov/2022/Nov/10/2003112742/-1/-1/0/CSI_SOFTWARE_MEMORY_SAFETY.PDF",
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
    result = DownloadResult(framework="nsa")

    result.notices.append(
        f"media.defense.gov blocks automated access (HTTP 403). "
        f"Download manually from {SOURCE_URL} and place files in "
        f"source-content/nsa/."
    )

    for filename, url in MANUAL_DOCS:
        result.manual_required.append((filename, url))

    return result
