# CompliGator 🐊

A self-contained Python tool for downloading, syncing, and normalizing compliance framework documentation from official sources. Tracks what you already have and only pulls what's new — no manual bookmarking, no hunting for PDFs.

> **What's in a name?** CompliGator = **Compli**ance Aggre**gator**. It snaps up compliance docs so you don't have to.

## Supported Frameworks

27 frameworks across 5 groups:

**NIST**
| Framework | Source |
|---|---|
| NIST Final Publications | csrc.nist.gov |
| NIST Draft Publications | csrc.nist.gov |
| NIST OSCAL Content | github.com/usnistgov/oscal-content |

**FedRAMP**
| Framework | Source |
|---|---|
| FedRAMP Rev 5 | fedramp.gov |
| FedRAMP Automation (GitHub) | github.com/GSA/fedramp-automation |
| GovRAMP | govrampsecurity.com |

**CISA**
| Framework | Source |
|---|---|
| CISA Binding Operational Directives | cisa.gov |
| CISA Emergency Directives | cisa.gov |
| CISA Zero Trust Maturity Model | cisa.gov |
| CISA Known Exploited Vulnerabilities | cisa.gov |

**DoD / Defense**
| Framework | Source |
|---|---|
| CMMC | dodcio.defense.gov |
| DISA STIGs | dl.dod.cyber.mil |
| DFARS / FAR Cybersecurity Clauses | acquisition.gov / ecfr.gov |
| DoD Zero Trust & Directives | dodcio.defense.gov |
| NSA Cybersecurity Advisories | nsa.gov (manual — WAF protected) |
| DCSA NISPOM (32 CFR Part 117) | ecfr.gov |
| CNSS Instructions & Policies | cnss.gov |

**Threat Intel**
| Framework | Source |
|---|---|
| MITRE ATT&CK (STIX 2.1) | github.com/mitre-attack/attack-stix-data |

**Frameworks**
| Framework | Source |
|---|---|
| OWASP ASVS | github.com/OWASP/ASVS |
| CSA Cloud Controls Matrix v4.1 | cloudsecurityalliance.org |
| CIS Controls v8 (Structured Data) | github.com/CISecurity/ControlsAssessmentSpecification |
| PCI DSS v4.0.1 | pcisecuritystandards.org |

**Policy / Regulatory**
| Framework | Source |
|---|---|
| HIPAA Security Rule | govinfo.gov |
| CJIS Security Policy | fbi.gov |
| OMB Cybersecurity Memoranda | whitehouse.gov |
| Executive Orders (Cybersecurity) | federalregister.gov |
| FTC Safeguards Rule (16 CFR Part 314) | ecfr.gov |

## Requirements

Python 3.9 or later. That's it — CompliGator handles everything else itself.

## Quick Start

```bash
python3 compligator.py
```

On first run, the tool will:

1. Create a local virtual environment (`.compligator-venv/`) next to the script
2. Install its own dependencies into that environment
3. Offer a one-time prompt to install the Playwright browser (~150 MB, needed for WAF-protected sites)
4. Launch the menu

Every run after that goes straight to the menu — no activation, no setup.

> **Debian/Ubuntu note:** If you see a message about `ensurepip`, run:
> ```bash
> sudo apt install python3.12-venv   # adjust version to match your Python
> ```
> Then run `python3 compligator.py` again.

## Usage

```
CompliGator
----------------------------------------------------
  1. NIST                     3 frameworks  last synced 2026-03-03
  2. FedRAMP                  3 frameworks  last synced 2026-03-03
  3. CISA                     3 frameworks  last synced 2026-03-02
  4. DoD / Defense            7 frameworks  last synced 2026-03-03
  5. Threat Intel             1 framework   last synced 2026-03-03
  6. Frameworks               4 frameworks  last synced 2026-03-03
  7. Policy / Regulatory      5 frameworks  last synced 2026-03-03

──────────────────────────────────────────────────────────────────────
  s = sync all  |  n = normalize all  |  c = check for updates  |  q = quit
──────────────────────────────────────────────────────────────────────
```

Select a group number to open it, then choose a framework to sync individually or press `s` to sync the whole group. From the main menu:

- **`s`** — sync all 26 frameworks
- **`n`** — normalize all downloaded documents
- **`c`** — quick scan: check for updates without downloading (see below)
- **`q`** — quit

### Quick Scan

Press `c` from the main menu to run a read-only update check against 4 high-churn targets without downloading anything:

```
Quick scan — checking for updates...

  CISA Known Exploited Vulnerabilities     up to date  (2 files)  last synced 2026-03-02
  FedRAMP Automation (GitHub)              up to date  (21 files)  last synced 2026-03-02
  NSA Cybersecurity Advisories             7 docs require manual download  never synced
  OWASP ASVS                               up to date  (4 files)  last synced 2026-03-02

  Note: NIST Drafts excluded from quick scan (requires full crawl — use Sync to update).
```

No files are written and the state file is unchanged after a scan.

## Sync Reports

After every sync — whether a single group or all frameworks — CompliGator prints a compact summary to the console and saves a full report to `reports/`:

```
  Sync report:

  FedRAMP                      36/36
  FedRAMP Automation (GitHub)  21/21
  GovRAMP                      34/34

  Report saved: reports/fedramp-sync-report-03.05.2026.md
```

Each report is a Markdown file named `<group>-sync-report-MM.DD.YYYY.md` (e.g. `complete-sync-report-03.05.2026.md` for a full sync). It contains:

- **Section 1 — Summary:** table of all synced frameworks with file counts and manual-download flags
- **Section 2+ — Per-framework detail:** per-file status table (Available / Missing) for every framework
- **Appendix A — Missing Documents:** error details and manual download URLs for anything that couldn't be retrieved automatically

The `reports/` directory is created automatically on first use.

## Normalization

The **Normalize** option converts downloaded documents into machine-readable formats suitable for AI pipelines, RAG systems, and MCP servers:

- **PDF files** — text extracted page-by-page via [pymupdf](https://pymupdf.readthedocs.io/)
- **HTML files** — main content extracted and structured by heading via BeautifulSoup
- **OSCAL JSON files** — catalog controls (statement + guidance prose) and profiles (control family listings) extracted as structured sections

Each source file produces two output files in `normalized-content/`:

| File | Purpose |
|---|---|
| `<stem>.md` | Human-readable Markdown with YAML frontmatter |
| `<stem>.json` | Machine-readable JSON with sections, full text, and metadata |

**JSON schema:**
```json
{
  "source_file": "NIST_SP-800-53_rev5_catalog.json",
  "framework": "nist-oscal",
  "extracted_at": "2026-02-28T14:30:00",
  "sections": [
    { "heading": "AC-1: Policy and Procedures", "level": 2, "content": "**Statement**\n..." }
  ],
  "full_text": "Complete concatenated text..."
}
```

> **Note:** DISA STIGs are excluded from normalization — their XCCDF XML structure requires a dedicated parser (planned for v2).

## How It Works

- **State tracking:** A `.compligator-state.json` file in `source-content/` records the hash and metadata of every downloaded file. On each sync, files are compared by hash — unchanged files are skipped.
- **Normalization:** Already-normalized files are skipped on re-runs. Run normalize again after syncing new documents to catch additions.
- **WAF fallback:** Several sources use WAF protection that blocks automated scrapers. CompliGator uses a three-tier strategy: plain HTTP → Playwright headless browser → curated fallback URL list. A notice is printed when the fallback list is used, along with the date it was last verified.
- **GitHub sources:** FedRAMP Automation, NIST OSCAL, MITRE ATT&CK, OWASP ASVS, and CIS Controls are discovered via the GitHub API. Set `GITHUB_TOKEN` in your environment to raise the unauthenticated rate limit from 60 to 5,000 requests/hour if needed.
- **DISA STIGs:** Downloads the full SRG/STIG archive ZIP from the DoD Cyber Exchange (~350 MB).

## Output Structure

```
reports/
├── complete-sync-report-MM.DD.YYYY.md
└── fedramp-sync-report-MM.DD.YYYY.md

source-content/
├── .compligator-state.json
├── fedramp/
├── fedramp-github/
│   ├── baselines/
│   ├── resources/
│   ├── templates/
│   └── guides/
├── govramp/
├── nist/
│   ├── final-pubs/
│   └── draft-pubs/
├── nist-oscal/
│   ├── SP800-53/rev5/
│   ├── SP800-171/rev3/
│   ├── SP800-218/ver1/
│   └── CSF/v2.0/
├── cisa-bod/
├── cisa-zt/
├── cisa-kev/
├── cmmc/
├── disa-stigs/
├── dfars-far/
├── dod-zt/
├── nsa/
├── nispom/
├── cnss/
├── mitre-attack/
├── owasp-asvs/
├── csa-ccm/
├── cis-controls/
├── pci-dss/
├── hipaa/
├── cjis/
├── omb/
├── executive-orders/
└── ftc-safeguards/
```

## Known Limitations

- **NSA Cybersecurity Advisories:** media.defense.gov blocks all automated download approaches. Files must be downloaded manually and dropped into `source-content/nsa/`. Quick scan reports the count of available advisories.
- **DISA STIGs:** The probe logic searches recent months for the current archive filename. If DISA changes their naming convention, the downloader may need an update.
- **CMMC:** If live scraping and Playwright both fail, a fallback URL list is used. The tool prints a notice with the date the list was last verified.
- **CISA BOD:** A small number of known BOD pages return 403 even via Playwright and remain in the known-URLs list for manual reference.
- **NIST:** A small number of publications have no direct download link on CSRC and will be skipped.
- **Normalization — scanned PDFs:** Image-only PDFs (no text layer) produce empty or minimal output. OCR is not included in v1.
- **OSCAL:** FedRAMP extension and template JSON files are not OSCAL catalogs or profiles and are intentionally skipped during normalization.
