"""Sync report generation for CompliGator."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from compligator.downloaders import ServiceDef
    from compligator.downloaders.base import DownloadResult


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s*/\s*", "-", s)
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def _files_cell(result: DownloadResult) -> str:
    ok = len(result.downloaded) + len(result.skipped)
    total = ok + len(result.errors)
    cell = f"{ok}/{total}"
    if result.manual_required:
        cell += f" (+{len(result.manual_required)} manual)"
    return cell


def _status_rows(result: DownloadResult) -> list[tuple[str, str]]:
    rows = []
    for name in result.downloaded:
        rows.append((name, "Available"))
    for name in result.skipped:
        rows.append((name, "Available"))
    for err in result.errors:
        rows.append((err[0], "Missing"))
    for name, _ in result.manual_required:
        rows.append((name, "Missing"))
    return rows


def build_report(
    results: list[tuple[ServiceDef, DownloadResult | None]],
    title: str,
) -> tuple[str, str]:
    """Returns (screen_text, full_markdown). screen_text = Section 1 only."""
    date_str = datetime.now(timezone.utc).strftime("%m.%d.%Y")

    # ── Section 1 (summary) ───────────────────────────────────────────────
    col_w = max(len(svc.label) for svc, _ in results)
    summary_rows = []
    for svc, result in results:
        cell = "error" if result is None else _files_cell(result)
        summary_rows.append(f"  {svc.label:<{col_w}}  {cell}")

    screen_text = "  Sync report:\n\n" + "\n".join(summary_rows) + "\n"

    # ── Markdown document ─────────────────────────────────────────────────
    md = [f"# {title} Report", "", f"Generated: {date_str}", ""]

    # Section 1
    md += ["## Section 1 — Summary", "", "| Framework | Files |", "| --- | --- |"]
    for svc, result in results:
        cell = "error" if result is None else _files_cell(result)
        md.append(f"| {svc.label} | {cell} |")
    md.append("")

    # Sections 2+ — per-framework detail
    any_missing = False
    for idx, (svc, result) in enumerate(results, start=2):
        md.append(f"## Section {idx} — {svc.label}")
        md.append("")
        if result is None:
            md += ["_Sync failed — no result data available._", ""]
            continue
        rows = _status_rows(result)
        if rows:
            md += ["| Document | Status |", "| --- | --- |"]
            for doc, status in rows:
                md.append(f"| {doc} | {status} |")
        else:
            md.append("_No documents attempted._")
        if result.errors or result.manual_required:
            any_missing = True
            md += ["", "_For missing documents, please see Appendix A for more details._"]
        md.append("")

    # Appendix A
    if any_missing:
        md += ["## Appendix A — Missing Documents", ""]
        for svc, result in results:
            if result is None or not (result.errors or result.manual_required):
                continue
            md += [f"### {svc.label}", ""]
            if result.notices:
                for notice in result.notices:
                    md += [notice, ""]
            else:
                md += [
                    "The following documents could not be retrieved automatically. "
                    "Please download them manually from the source URLs provided.",
                    "",
                ]
            md += ["| Document | Source |", "| --- | --- |"]
            for err in result.errors:
                name, msg = err[0], err[1]
                url = err[2] if len(err) > 2 else ""
                source = f"[{url}]({url})" if url else f"Error: {msg}"
                md.append(f"| {name} | {source} |")
            for name, url in result.manual_required:
                md.append(f"| {name} | {url if url else 'manually supplied'} |")
            md.append("")

    return screen_text, "\n".join(md)


def save_report(full_md: str, report_dir: Path, slug: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%m.%d.%Y")
    path = report_dir / f"{slug}-sync-report-{date_str}.md"
    path.write_text(full_md, encoding="utf-8")
    return path
