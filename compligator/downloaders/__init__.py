"""Downloader registry — maps CLI framework keys to runner functions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from . import (
    cis_benchmarks,
    cis_controls,
    cisa_bod,
    cisa_ed,
    cisa_kev,
    cisa_zt,
    cjis,
    cmmc,
    cnss,
    common_criteria,
    csa_ccm,
    dfars_far,
    disa,
    dod_8140,
    dod_cloud,
    dod_devsecops,
    dod_icam,
    dod_zt,
    executive_orders,
    fedramp,
    ftc_safeguards,
    gdpr,
    govramp,
    hipaa,
    iec62443,
    iso27k,
    mitre_attack,
    nispom,
    nist,
    nist_oscal,
    nist_privacy,
    nsa,
    omb,
    owasp_asvs,
    pci_dss,
    soc2,
)
from .base import DownloadResult

if TYPE_CHECKING:
    from compligator.state import StateFile


@dataclass(frozen=True)
class ServiceDef:
    key: str
    label: str
    runner: Callable[[Path, bool, bool, Optional["StateFile"]], DownloadResult]
    subdir: str  # path prefix under output_dir used by this downloader
    group: str  # top-level menu group this service belongs to
    acquisition: str = "auto"  # "auto" | "mixed" | "manual"


# Ordered display groups for the top-level menu.
GROUPS: list[str] = [
    "NIST",
    "FedRAMP",
    "CISA",
    "DoD / Defense",
    "Threat Intel",
    "Frameworks",
    "Policy / Regulatory",
    "International Standards",
]

SERVICES: list[ServiceDef] = [
    # ── NIST ──────────────────────────────────────────────────────────────────
    ServiceDef(
        "nist-finals",
        "NIST Final Publications",
        nist.run_finals,
        "nist/final-pubs",
        "NIST",
    ),
    ServiceDef(
        "nist-drafts",
        "NIST Draft Publications",
        nist.run_drafts,
        "nist/draft-pubs",
        "NIST",
    ),
    ServiceDef("nist-oscal", "NIST OSCAL Content", nist_oscal.run, "nist-oscal", "NIST"),
    ServiceDef(
        "nist-privacy",
        "NIST Privacy Framework v1.0",
        nist_privacy.run,
        "nist-privacy",
        "NIST",
    ),
    # ── FedRAMP ───────────────────────────────────────────────────────────────
    ServiceDef("fedramp", "FedRAMP", fedramp.run, "fedramp", "FedRAMP"),
    ServiceDef("govramp", "GovRAMP", govramp.run, "govramp", "FedRAMP"),
    # ── CISA ──────────────────────────────────────────────────────────────────
    ServiceDef(
        "cisa-bod",
        "CISA Binding Operational Directives",
        cisa_bod.run,
        "cisa-bod",
        "CISA",
    ),
    ServiceDef(
        "cisa-ed",
        "CISA Emergency Directives",
        cisa_ed.run,
        "cisa-ed",
        "CISA",
    ),
    ServiceDef("cisa-zt", "CISA Zero Trust Maturity Model", cisa_zt.run, "cisa-zt", "CISA"),
    ServiceDef(
        "cisa-kev",
        "CISA Known Exploited Vulnerabilities",
        cisa_kev.run,
        "cisa-kev",
        "CISA",
    ),
    # ── DoD / Defense ─────────────────────────────────────────────────────────
    ServiceDef("cmmc", "CMMC", cmmc.run, "cmmc", "DoD / Defense", acquisition="mixed"),
    ServiceDef("disa", "DISA STIGs", disa.run, "disa-stigs", "DoD / Defense"),
    ServiceDef(
        "dfars-far",
        "DFARS / FAR Cybersecurity Clauses",
        dfars_far.run,
        "dfars-far",
        "DoD / Defense",
    ),
    ServiceDef(
        "dod-zt",
        "DoD Zero Trust & Directives",
        dod_zt.run,
        "dod-zt",
        "DoD / Defense",
        acquisition="mixed",
    ),
    ServiceDef(
        "dod-devsecops",
        "DoD DevSecOps & cATO",
        dod_devsecops.run,
        "dod-devsecops",
        "DoD / Defense",
    ),
    ServiceDef("dod-icam", "DoD ICAM", dod_icam.run, "dod-icam", "DoD / Defense"),
    ServiceDef(
        "dod-8140",
        "DoD 8140 Cyberspace Workforce",
        dod_8140.run,
        "dod-8140",
        "DoD / Defense",
    ),
    ServiceDef(
        "dod-cloud",
        "DoD Cloud Security",
        dod_cloud.run,
        "dod-cloud",
        "DoD / Defense",
    ),
    ServiceDef(
        "nsa",
        "NSA Cybersecurity Advisories",
        nsa.run,
        "nsa",
        "DoD / Defense",
        acquisition="manual",
    ),
    ServiceDef(
        "nispom",
        "DCSA NISPOM (32 CFR Part 117)",
        nispom.run,
        "nispom",
        "DoD / Defense",
        acquisition="mixed",
    ),
    ServiceDef("cnss", "CNSS Instructions & Policies", cnss.run, "cnss", "DoD / Defense"),
    # ── Threat Intel ──────────────────────────────────────────────────────────
    ServiceDef(
        "mitre-attack",
        "MITRE ATT&CK (STIX 2.1)",
        mitre_attack.run,
        "mitre-attack",
        "Threat Intel",
    ),
    # ── Frameworks ────────────────────────────────────────────────────────────
    ServiceDef("owasp-asvs", "OWASP ASVS", owasp_asvs.run, "owasp-asvs", "Frameworks"),
    ServiceDef("csa-ccm", "CSA Cloud Controls Matrix v4.1", csa_ccm.run, "csa-ccm", "Frameworks"),
    ServiceDef(
        "cis-controls",
        "CIS Controls v8 (Structured Data)",
        cis_controls.run,
        "cis-controls",
        "Frameworks",
    ),
    ServiceDef(
        "pci-dss",
        "PCI DSS v4.0.1",
        pci_dss.run,
        "pci-dss",
        "Frameworks",
        acquisition="mixed",
    ),
    ServiceDef("soc2", "SOC 2 / AICPA Trust Services Criteria", soc2.run, "soc2", "Frameworks"),
    ServiceDef(
        "cis-benchmarks",
        "CIS Benchmarks",
        cis_benchmarks.run,
        "cis-benchmarks",
        "Frameworks",
    ),
    # ── Policy / Regulatory ───────────────────────────────────────────────────
    ServiceDef("hipaa", "HIPAA Security Rule", hipaa.run, "hipaa", "Policy / Regulatory"),
    ServiceDef("cjis", "CJIS Security Policy", cjis.run, "cjis", "Policy / Regulatory"),
    ServiceDef("omb", "OMB Cybersecurity Memoranda", omb.run, "omb", "Policy / Regulatory"),
    ServiceDef(
        "executive-orders",
        "Executive Orders (Cybersecurity)",
        executive_orders.run,
        "executive-orders",
        "Policy / Regulatory",
    ),
    ServiceDef(
        "ftc-safeguards",
        "FTC Safeguards Rule (16 CFR Part 314)",
        ftc_safeguards.run,
        "ftc-safeguards",
        "Policy / Regulatory",
    ),
    # ── International Standards ───────────────────────────────────────────────
    ServiceDef(
        "iso27k",
        "ISO/IEC 27000 Series",
        iso27k.run,
        "iso27k",
        "International Standards",
        acquisition="manual",
    ),
    ServiceDef(
        "iec62443",
        "IEC 62443 (IACS Security)",
        iec62443.run,
        "iec62443",
        "International Standards",
        acquisition="manual",
    ),
    ServiceDef(
        "common-criteria",
        "Common Criteria (ISO/IEC 15408)",
        common_criteria.run,
        "common-criteria",
        "International Standards",
    ),
    ServiceDef(
        "gdpr",
        "GDPR (Regulation EU 2016/679)",
        gdpr.run,
        "gdpr",
        "International Standards",
    ),
]

SERVICES_BY_KEY: dict[str, ServiceDef] = {s.key: s for s in SERVICES}
SERVICES_BY_GROUP: dict[str, list[ServiceDef]] = {
    g: [s for s in SERVICES if s.group == g] for g in GROUPS
}
