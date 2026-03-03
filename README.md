# CompliGator 🐊

A self-contained Python tool for downloading, syncing, and normalizing compliance framework documentation from official sources. Tracks what you already have and only pulls what's new — no manual bookmarking, no hunting for PDFs.

> **What's in a name?** CompliGator = **Compli**ance Aggre**gator**. It snaps up compliance docs so you don't have to.

## Supported Frameworks

| Framework | Source | Coverage |
|---|---|---|
| FedRAMP Rev 5 | fedramp.gov | Documents and templates |
| FedRAMP Automation (GitHub) | github.com/GSA/fedramp-automation | OSCAL baselines, resources, templates, guides |
| NIST Final Publications | csrc.nist.gov | SP, CSWP, AI series |
| NIST Draft Publications | csrc.nist.gov | IPD, 2PD series |
| NIST OSCAL Content | github.com/usnistgov/oscal-content | SP 800-53, SP 800-171, SP 800-218, CSF v2.0 |
| CMMC | dodcio.defense.gov | Full document library |
| DISA STIGs | dl.dod.cyber.mil | Full SRG/STIG library (ZIP) |
| CISA Binding Operational Directives | cisa.gov | All BODs and implementation guidance (HTML) |

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
   1. FedRAMP                          36 files   37.5 MB  last synced 2026-02-28
   2. FedRAMP Automation (GitHub)      21 files   33.7 MB  last synced 2026-02-28
   3. NIST Final Publications         653 files    2.1 GB  last synced 2026-02-28
   4. NIST Draft Publications          92 files  146.0 MB  last synced 2026-02-28
   5. NIST OSCAL Content               12 files   23.8 MB  last synced 2026-02-28
   6. CMMC                             17 files   18.3 MB  last synced 2026-02-28
   7. DISA STIGs                        1 files  350.0 MB  last synced 2026-02-28
   8. CISA Binding Operational Directives  14 files    0.5 MB  last synced 2026-02-28

   9. Sync All
  10. Normalize Downloaded Documents
   0. Quit

Select:
```

Select a number to sync a single framework, choose **Sync All** to pull everything at once, or choose **Normalize Downloaded Documents** to convert your downloads to Markdown and JSON.

Downloaded files land in `source-content/<framework>/`. The tool skips files it already has and only fetches what's changed or new.

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

> **Note:** DISA STIGs are excluded from v1 normalization — their XCCDF XML structure requires a dedicated parser.

## How It Works

- **State tracking:** A `.compligator-state.json` file in `source-content/` records the hash and metadata of every downloaded file. On each sync, files are compared by hash — unchanged files are skipped.
- **Normalization:** Already-normalized files are skipped on re-runs. Run normalize again after syncing new documents to catch additions.
- **WAF fallback:** Several sources use WAF protection that blocks automated scrapers. CompliGator uses a three-tier strategy: plain HTTP → Playwright headless browser → curated fallback URL list. A notice is printed when the fallback list is used, along with the date it was last verified.
- **GitHub sources:** FedRAMP Automation and NIST OSCAL content are discovered via the GitHub API and downloaded from `raw.githubusercontent.com`. Set `GITHUB_TOKEN` in your environment to raise the unauthenticated rate limit from 60 to 5,000 requests/hour if needed.
- **DISA STIGs:** Downloads the full SRG/STIG archive ZIP from the DoD Cyber Exchange (~350 MB).

## Output Structure

```
source-content/
├── .compligator-state.json
├── fedramp/
├── fedramp-github/
│   ├── baselines/
│   ├── resources/
│   ├── templates/
│   └── guides/
├── nist/
│   ├── final-pubs/
│   └── draft-pubs/
├── nist-oscal/
│   ├── SP800-53/rev5/
│   ├── SP800-171/rev3/
│   ├── SP800-218/ver1/
│   └── CSF/v2.0/
├── cmmc/
├── disa-stigs/
└── cisa-bod/

normalized-content/
├── fedramp/
├── fedramp-github/
│   └── baselines/
├── nist/
│   ├── final-pubs/
│   └── draft-pubs/
├── nist-oscal/
│   ├── SP800-53/rev5/
│   └── ...
├── cmmc/
└── cisa-bod/
```

## Manually Supplied Frameworks

Some frameworks cannot be automatically downloaded due to paywalls or registration requirements. Placeholder directories with instructions are included for:

- `source-content/hipaa/` — HIPAA Security Rule (free, no automated downloader yet)
- `source-content/iso-27k/` — ISO/IEC 27001 & 27002 (paywalled)
- `source-content/pci-dss/` — PCI DSS v4.0 (registration required)
- `source-content/cis-controls/` — CIS Controls v8 (registration required)
- `source-content/soc2/` — SOC 2 TSC (paywalled)

Drop PDFs into these directories — CompliGator's normalize command will pick them up.

## Known Limitations

- **DISA STIGs:** The probe logic searches recent months for the current archive filename. If DISA changes their naming convention, the downloader may need an update.
- **CMMC:** If live scraping and Playwright both fail, a fallback URL list is used. The tool prints a notice with the date the list was last verified.
- **CISA BOD:** 3 of 17 known BOD pages use an older URL format that returns 403 even via Playwright. They remain in the known-URLs list for manual reference.
- **NIST:** A small number of publications have no direct download link on CSRC and will be skipped.
- **Normalization — scanned PDFs:** Image-only PDFs (no text layer) produce empty or minimal output. OCR is not included in v1.
- **OSCAL:** FedRAMP extension and template JSON files are not OSCAL catalogs or profiles and are intentionally skipped during normalization.
