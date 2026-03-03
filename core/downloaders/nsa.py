"""NSA Cybersecurity Advisories & Guidance downloader.

Downloads key NSA cybersecurity advisory PDFs from media.defense.gov.

NSA publishes advisories and guidance documents at media.defense.gov.
The nsa.gov/Cybersecurity/Advisories page is JavaScript-rendered and not
reliably scrapeable; direct known URLs are used instead.

The nsacyber GitHub org (github.com/nsacyber) hosts individual security
tool repos but does not maintain a consolidated publications release.
Individual repos with notable guidance (e.g., Hardware-and-Firmware-
Security-Guidance) may be added as separate entries if needed.

Set the GITHUB_TOKEN environment variable to raise the unauthenticated
GitHub API rate limit from 60 to 5,000 requests/hour if GitHub sources
are added in the future.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.state import StateFile

from .base import (
    DownloadResult,
    playwright_navigate_file,
)

SOURCE_URL = "https://www.nsa.gov/Press-Room/Cybersecurity-Advisories-Guidance/"

# Date the KNOWN_DOCS list was last manually verified
KNOWN_DOCS_VERIFIED = "2026-03-02"

# Curated list of key NSA cybersecurity advisory PDFs from media.defense.gov.
# (filename, url)
KNOWN_DOCS: list[tuple[str, str]] = [
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
    dest = output_dir / "nsa"
    result = DownloadResult(framework="nsa")

    result.notices.append(
        f"Using curated advisory list (last verified {KNOWN_DOCS_VERIFIED}). "
        f"Check {SOURCE_URL} for new advisories not yet in this list."
    )

    if dry_run:
        for filename, _url in KNOWN_DOCS:
            target = dest / filename
            if not force and target.exists() and target.stat().st_size > 0:
                result.skipped.append(filename)
            else:
                result.downloaded.append(filename)
        return result

    dest.mkdir(parents=True, exist_ok=True)

    for filename, url in KNOWN_DOCS:
        target = dest / filename
        ok, msg = playwright_navigate_file(url, target, force=force, state=state)
        if msg == "skipped":
            result.skipped.append(filename)
        elif ok:
            result.downloaded.append(filename)
        else:
            result.errors.append((filename, msg))

    return result
