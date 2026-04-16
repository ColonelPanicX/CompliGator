"""CMMC download diagnostic script.

Runs each step of the CMMC fetch strategy independently and prints
exactly what happens at each point. Run from the repo root:

    python scripts/diag-cmmc.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap — ensure we can import core/
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).parent.parent))

import shutil
import subprocess
import tempfile

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://dodcio.defense.gov/cmmc/Resources-Documentation/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
SECTION_MODULES = {
    "internal": "dnn_ctr136430_ModuleContent",
    "external": "dnn_ctr136428_ModuleContent",
}
SAMPLE_PDF_URLS = [
    "https://dodcio.defense.gov/Portals/0/Documents/CMMC/CMMC-101-Nov2025.pdf",
    "https://dodcio.defense.gov/Portals/0/Documents/CMMC/ModelOverviewv2.pdf",
    "https://dodcio.defense.gov/Portals/0/Documents/CMMC/CMMC-FAQsv4.pdf",
]

SEP = "-" * 60


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ---------------------------------------------------------------------------
# Step 1: Plain requests — index page
# ---------------------------------------------------------------------------

section("STEP 1: Plain requests → index page")
try:
    resp = requests.get(SOURCE_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    print(f"  Status     : {resp.status_code}")
    print(f"  Content-Type: {resp.headers.get('Content-Type', 'n/a')}")
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("title")
    print(f"  Page title : {title.get_text().strip() if title else '(no title)'}")
    for section_key, module_id in SECTION_MODULES.items():
        container = soup.find(id=module_id)
        print(f"  Module [{section_key}] id={module_id}: {'FOUND' if container else 'NOT FOUND'}")
        if container:
            anchors = container.find_all("a", href=True)
            print(f"    → {len(anchors)} anchor(s)")
            for a in anchors[:5]:
                print(f"      {a['href']}")
            if len(anchors) > 5:
                print(f"      ... and {len(anchors) - 5} more")
except Exception as exc:
    print(f"  ERROR: {exc}")

# ---------------------------------------------------------------------------
# Step 2: Playwright — index page
# ---------------------------------------------------------------------------

section("STEP 2: Playwright → index page")
try:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(user_agent=USER_AGENT)
        response = page.goto(SOURCE_URL, wait_until="networkidle", timeout=30000)
        print(f"  Status     : {response.status if response else 'n/a'}")
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title")
    print(f"  Page title : {title.get_text().strip() if title else '(no title)'}")
    for section_key, module_id in SECTION_MODULES.items():
        container = soup.find(id=module_id)
        print(f"  Module [{section_key}] id={module_id}: {'FOUND' if container else 'NOT FOUND'}")
        if container:
            anchors = container.find_all("a", href=True)
            print(f"    → {len(anchors)} anchor(s)")
            for a in anchors[:5]:
                print(f"      {a['href']}")
            if len(anchors) > 5:
                print(f"      ... and {len(anchors) - 5} more")
except ImportError:
    print("  Playwright not installed — skipping")
except Exception as exc:
    print(f"  ERROR: {exc}")

# ---------------------------------------------------------------------------
# Step 3: Direct PDF downloads — plain requests, no referer
# ---------------------------------------------------------------------------

section("STEP 3: Direct PDF downloads — plain requests, no referer")
session = requests.Session()
for url in SAMPLE_PDF_URLS:
    try:
        resp = session.head(
            url, headers={"User-Agent": USER_AGENT}, timeout=15, allow_redirects=True
        )
        print(f"  {resp.status_code}  {url}")
    except Exception as exc:
        print(f"  ERROR  {url}  ({exc})")

# ---------------------------------------------------------------------------
# Step 4: Direct PDF downloads — with Referer header
# ---------------------------------------------------------------------------

section("STEP 4: Direct PDF downloads — with Referer: SOURCE_URL")
for url in SAMPLE_PDF_URLS:
    try:
        resp = session.head(
            url,
            headers={"User-Agent": USER_AGENT, "Referer": SOURCE_URL},
            timeout=15,
            allow_redirects=True,
        )
        print(f"  {resp.status_code}  {url}")
    except Exception as exc:
        print(f"  ERROR  {url}  ({exc})")

# ---------------------------------------------------------------------------
# Step 5: Direct PDF downloads — with Playwright (full browser)
# ---------------------------------------------------------------------------

section("STEP 5: Direct PDF downloads — Playwright navigate")
try:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        for url in SAMPLE_PDF_URLS:
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                response = page.goto(url, timeout=20000)
                status = response.status if response else "n/a"
                content_type = response.headers.get("content-type", "n/a") if response else "n/a"
                print(f"  {status}  [{content_type}]  {url}")
                page.close()
            except Exception as exc:
                print(f"  ERROR  {url}  ({exc})")
        browser.close()
except ImportError:
    print("  Playwright not installed — skipping")
except Exception as exc:
    print(f"  ERROR: {exc}")


# ---------------------------------------------------------------------------
# Step 6: Direct PDF downloads — curl subprocess
# ---------------------------------------------------------------------------

section("STEP 6: Direct PDF downloads — curl subprocess")
if not shutil.which("curl"):
    print("  curl not found on PATH — skipping")
else:
    with tempfile.TemporaryDirectory() as tmpdir:
        for url in SAMPLE_PDF_URLS:
            dest = Path(tmpdir) / Path(url).name
            try:
                result = subprocess.run(
                    ["curl", "-L", "-s", "-w", "%{http_code}", "-o", str(dest), url],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                http_code = result.stdout.strip()
                size = dest.stat().st_size if dest.exists() else 0
                print(f"  HTTP {http_code}  {size:,} bytes  {url}")
            except Exception as exc:
                print(f"  ERROR  {url}  ({exc})")

print(f"\n{SEP}")
print("  Diagnostic complete.")
print(SEP)
