#!/usr/bin/env python3
"""UAT test runner for CompliGator downloaders.

Calls each downloader's run() directly (bypasses the interactive CLI) and
prints a structured pass/fail results table. Large-file frameworks are tested
in dry-run mode to avoid multi-GB downloads during automated UAT.

Usage:
    # Tier 2 only (default — matches current work-in-progress)
    .compligator-venv/bin/python scripts/uat-downloaders.py

    # Specific tier
    .compligator-venv/bin/python scripts/uat-downloaders.py --tier 1

    # Specific frameworks
    .compligator-venv/bin/python scripts/uat-downloaders.py --keys nsa,mitre-attack,govramp

    # All registered frameworks
    .compligator-venv/bin/python scripts/uat-downloaders.py --all

    # Custom output dir (default: test-output/uat-<timestamp>/)
    .compligator-venv/bin/python scripts/uat-downloaders.py --output-dir /tmp/uat
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.downloaders import SERVICES, SERVICES_BY_KEY  # noqa: E402

# Frameworks that are too large for live automated UAT — tested in dry-run mode.
# Dry-run still exercises API/scrape discovery logic; it just skips the actual download.
DRY_RUN_KEYS: set[str] = {
    "nist-finals",     # 2.1 GB
    "nist-drafts",     # 146 MB
    "disa",            # 350 MB
    "mitre-attack",    # 50–200 MB
    "fedramp-github",  # 34 MB
}

# Tier membership — used by --tier flag
TIER_KEYS: dict[int, set[str]] = {
    1: {"cisa-zt", "cisa-kev", "hipaa", "cjis", "owasp-asvs", "omb", "dod-zt"},
    2: {"govramp", "csa-ccm", "executive-orders", "dfars-far", "nsa", "mitre-attack"},
    3: {"ftc-safeguards", "cnss", "pci-dss", "nispom", "cis-controls"},
}

# Column widths
_W_LABEL = 36
_W_MODE  = 8
_W_RSLT  = 6
_W_FILES = 8
_W_ERRS  = 5


def _label(text: str, width: int) -> str:
    return text[:width - 2] + ".." if len(text) > width else text


def _result(downloaded: int, skipped: int, errors: int, manual: int) -> str:
    if errors > 0 and downloaded == 0 and skipped == 0:
        return "FAIL"
    if errors > 0:
        return "WARN"
    if downloaded == 0 and skipped == 0 and manual == 0:
        return "FAIL"
    return "PASS"


def run_uat(keys: list[str], output_dir: Path) -> int:
    """Run UAT for the given framework keys. Returns number of failures."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  Output : {output_dir}")
    print(f"  Count  : {len(keys)} framework(s)\n")

    header = (
        f"  {'Framework':<{_W_LABEL}}  {'Mode':<{_W_MODE}}  {'Result':<{_W_RSLT}}"
        f"  {'DL/Skip':>{_W_FILES}}  {'Err':>{_W_ERRS}}  Notes"
    )
    sep = "  " + "-" * 92
    print(header)
    print(sep)

    failures = 0

    for key in keys:
        svc = SERVICES_BY_KEY.get(key)
        if svc is None:
            label = _label(f"[unknown: {key}]", _W_LABEL)
            print(f"  {label:<{_W_LABEL}}  {'—':<{_W_MODE}}  {'SKIP':<{_W_RSLT}}")
            continue

        dry_run = key in DRY_RUN_KEYS
        mode = "dry-run" if dry_run else "live"
        fw_label = _label(svc.label, _W_LABEL)

        try:
            t0 = time.monotonic()
            result = svc.runner(output_dir, dry_run, False, None)
            elapsed = time.monotonic() - t0
        except Exception as exc:  # noqa: BLE001
            print(
                f"  {fw_label:<{_W_LABEL}}  {mode:<{_W_MODE}}  {'FAIL':<{_W_RSLT}}"
                f"  {'—':>{_W_FILES}}  {'—':>{_W_ERRS}}  exception: {exc}"
            )
            failures += 1
            continue

        dl  = len(result.downloaded)
        sk  = len(result.skipped)
        err = len(result.errors)
        man = len(result.manual_required)
        verdict = _result(dl, sk, err, man)

        # Build notes: inline errors (first 2) + fallback notice flag
        notes: list[str] = []
        for fname, msg in result.errors[:2]:
            short = fname.replace(".pdf", "").replace(".html", "").replace(".json", "")
            notes.append(f"{short}: {msg}")
        if len(result.errors) > 2:
            notes.append(f"+{len(result.errors) - 2} more errors")
        for notice in result.notices:
            if "fallback" in notice.lower():
                notes.append("fallback (expected)")
                break

        files_col = f"{dl}/{sk}s" if sk else (f"{man}m" if man and dl == 0 else str(dl))
        timing = f"{elapsed:.1f}s"
        notes_str = "; ".join(notes) if notes else timing

        print(
            f"  {fw_label:<{_W_LABEL}}  {mode:<{_W_MODE}}  {verdict:<{_W_RSLT}}"
            f"  {files_col:>{_W_FILES}}  {err:>{_W_ERRS}}  {notes_str}"
        )

        if verdict == "FAIL":
            failures += 1

    print(sep)
    status = "ALL PASS" if failures == 0 else f"{failures} FAILURE(S)"
    print(f"\n  {status}\n")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CompliGator downloader UAT runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tier", type=int, choices=[1, 2, 3], help="Run all frameworks in a tier")
    group.add_argument("--keys", metavar="K1,K2", help="Comma-separated framework keys")
    group.add_argument("--all", action="store_true", dest="run_all", help="Run all frameworks")
    parser.add_argument(
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="Download destination (default: test-output/uat-<timestamp>/)",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="Print all registered framework keys and exit",
    )
    args = parser.parse_args()

    if args.list_keys:
        print("\nRegistered framework keys:")
        for svc in SERVICES:
            dry = " [dry-run in UAT]" if svc.key in DRY_RUN_KEYS else ""
            tier = ""
            for t, keys in TIER_KEYS.items():
                if svc.key in keys:
                    tier = f" [tier {t}]"
            print(f"  {svc.key:<26} {svc.label}{tier}{dry}")
        print()
        sys.exit(0)

    # Resolve which keys to run
    if args.run_all:
        keys = [s.key for s in SERVICES]
    elif args.keys:
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    elif args.tier:
        tier_set = TIER_KEYS.get(args.tier, set())
        keys = [s.key for s in SERVICES if s.key in tier_set]
    else:
        # Default: Tier 3 (current work-in-progress)
        tier_set = TIER_KEYS[3]
        keys = [s.key for s in SERVICES if s.key in tier_set]

    if not keys:
        print("No frameworks matched. Use --all, --tier N, --keys k1,k2, or --list-keys.")
        sys.exit(1)

    if args.output_dir:
        output_dir = args.output_dir
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = ROOT / "test-output" / f"uat-{ts}"

    failures = run_uat(keys, output_dir)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
