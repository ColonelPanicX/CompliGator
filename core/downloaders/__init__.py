"""Downloader registry — maps CLI framework keys to runner functions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from . import (
    cis_controls,
    cisa_bod,
    cisa_kev,
    cisa_zt,
    cjis,
    cmmc,
    cnss,
    csa_ccm,
    dfars_far,
    disa,
    dod_zt,
    executive_orders,
    fedramp,
    fedramp_github,
    ftc_safeguards,
    govramp,
    hipaa,
    mitre_attack,
    nispom,
    nist,
    nist_oscal,
    nsa,
    omb,
    owasp_asvs,
    pci_dss,
)
from .base import DownloadResult

if TYPE_CHECKING:
    from core.state import StateFile


@dataclass(frozen=True)
class ServiceDef:
    key: str
    label: str
    runner: Callable[[Path, bool, bool, Optional["StateFile"]], DownloadResult]
    subdir: str  # path prefix under output_dir used by this downloader
    group: str   # top-level menu group this service belongs to


# Ordered display groups for the top-level menu.
GROUPS: list[str] = [
    "NIST",
    "FedRAMP",
    "CISA",
    "DoD / Defense",
    "Threat Intel",
    "Frameworks",
    "Policy / Regulatory",
]

SERVICES: list[ServiceDef] = [
    # ── NIST ──────────────────────────────────────────────────────────────────
    ServiceDef(
        "nist-finals", "NIST Final Publications",
        nist.run_finals, "nist/final-pubs", "NIST",
    ),
    ServiceDef(
        "nist-drafts", "NIST Draft Publications",
        nist.run_drafts, "nist/draft-pubs", "NIST",
    ),
    ServiceDef("nist-oscal", "NIST OSCAL Content", nist_oscal.run, "nist-oscal", "NIST"),
    # ── FedRAMP ───────────────────────────────────────────────────────────────
    ServiceDef("fedramp", "FedRAMP", fedramp.run, "fedramp", "FedRAMP"),
    ServiceDef(
        "fedramp-github", "FedRAMP Automation (GitHub)",
        fedramp_github.run, "fedramp-github", "FedRAMP",
    ),
    ServiceDef("govramp", "GovRAMP", govramp.run, "govramp", "FedRAMP"),
    # ── CISA ──────────────────────────────────────────────────────────────────
    ServiceDef(
        "cisa-bod", "CISA Binding Operational Directives",
        cisa_bod.run, "cisa-bod", "CISA",
    ),
    ServiceDef("cisa-zt", "CISA Zero Trust Maturity Model", cisa_zt.run, "cisa-zt", "CISA"),
    ServiceDef(
        "cisa-kev", "CISA Known Exploited Vulnerabilities",
        cisa_kev.run, "cisa-kev", "CISA",
    ),
    # ── DoD / Defense ─────────────────────────────────────────────────────────
    ServiceDef("cmmc", "CMMC", cmmc.run, "cmmc", "DoD / Defense"),
    ServiceDef("disa", "DISA STIGs", disa.run, "disa-stigs", "DoD / Defense"),
    ServiceDef(
        "dfars-far", "DFARS / FAR Cybersecurity Clauses",
        dfars_far.run, "dfars-far", "DoD / Defense",
    ),
    ServiceDef("dod-zt", "DoD Zero Trust & Directives", dod_zt.run, "dod-zt", "DoD / Defense"),
    ServiceDef("nsa", "NSA Cybersecurity Advisories", nsa.run, "nsa", "DoD / Defense"),
    ServiceDef(
        "nispom", "DCSA NISPOM (32 CFR Part 117)",
        nispom.run, "nispom", "DoD / Defense",
    ),
    ServiceDef("cnss", "CNSS Instructions & Policies", cnss.run, "cnss", "DoD / Defense"),
    # ── Threat Intel ──────────────────────────────────────────────────────────
    ServiceDef(
        "mitre-attack", "MITRE ATT&CK (STIX 2.1)",
        mitre_attack.run, "mitre-attack", "Threat Intel",
    ),
    # ── Frameworks ────────────────────────────────────────────────────────────
    ServiceDef("owasp-asvs", "OWASP ASVS", owasp_asvs.run, "owasp-asvs", "Frameworks"),
    ServiceDef("csa-ccm", "CSA Cloud Controls Matrix v4.1", csa_ccm.run, "csa-ccm", "Frameworks"),
    ServiceDef(
        "cis-controls", "CIS Controls v8 (Structured Data)",
        cis_controls.run, "cis-controls", "Frameworks",
    ),
    ServiceDef("pci-dss", "PCI DSS v4.0.1", pci_dss.run, "pci-dss", "Frameworks"),
    # ── Policy / Regulatory ───────────────────────────────────────────────────
    ServiceDef("hipaa", "HIPAA Security Rule", hipaa.run, "hipaa", "Policy / Regulatory"),
    ServiceDef("cjis", "CJIS Security Policy", cjis.run, "cjis", "Policy / Regulatory"),
    ServiceDef("omb", "OMB Cybersecurity Memoranda", omb.run, "omb", "Policy / Regulatory"),
    ServiceDef(
        "executive-orders", "Executive Orders (Cybersecurity)",
        executive_orders.run, "executive-orders", "Policy / Regulatory",
    ),
    ServiceDef(
        "ftc-safeguards", "FTC Safeguards Rule (16 CFR Part 314)",
        ftc_safeguards.run, "ftc-safeguards", "Policy / Regulatory",
    ),
]

SERVICES_BY_KEY: dict[str, ServiceDef] = {s.key: s for s in SERVICES}
SERVICES_BY_GROUP: dict[str, list[ServiceDef]] = {
    g: [s for s in SERVICES if s.group == g] for g in GROUPS
}
