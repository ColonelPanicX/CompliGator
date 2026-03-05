"""CompliGator — compliance document aggregator."""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check — must run before any third-party imports
# ---------------------------------------------------------------------------

def _check_dependencies() -> None:
    """Verify required packages are installed and print install instructions if not."""
    required = [
        ("requests",       "requests"),
        ("beautifulsoup4", "bs4"),
        ("pymupdf",        "fitz"),
    ]
    missing_pkgs = []
    for pkg_name, import_name in required:
        try:
            __import__(import_name)
        except ImportError:
            missing_pkgs.append(pkg_name)

    if missing_pkgs:
        print("CompliGator is missing required packages:\n")
        for pkg in missing_pkgs:
            print(f"  - {pkg}")
        print()
        print("Run the tool via compligator.py to install automatically:")
        print("  python3 compligator.py")
        print()
        sys.exit(1)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

_BAR = "─" * 70


def _human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _svc_info(svc, entries: dict, state) -> str:
    """Return a short sync-status string for one service."""
    prefix = svc.subdir + "/"
    svc_entries = {k: v for k, v in entries.items() if k.startswith(prefix)}
    if svc_entries:
        count = len(svc_entries)
        size  = _human_size(sum(e["size"] for e in svc_entries.values()))
        last  = max(e["recorded_at"] for e in svc_entries.values())[:10]
        total = state.get_service_total(svc.key)
        count_str = f"{count}/{total}" if total else str(count)
        return f"{count_str} files  {size}  last synced {last}"
    return "never synced"


def _group_info(group_svcs: list, entries: dict) -> str:
    """Return a short sync-status string for a group of services."""
    dates = []
    for svc in group_svcs:
        prefix = svc.subdir + "/"
        svc_entries = {k: v for k, v in entries.items() if k.startswith(prefix)}
        if svc_entries:
            dates.append(max(e["recorded_at"] for e in svc_entries.values())[:10])
    n = len(group_svcs)
    noun = "framework" if n == 1 else "frameworks"
    if dates:
        return f"{n} {noun}  last synced {max(dates)}"
    return f"{n} {noun}  never synced"


def _print_group_menu(groups: list[str], services_by_group: dict, entries: dict) -> None:
    print()
    print("CompliGator")
    print("-" * 52)
    for i, group in enumerate(groups, 1):
        info = _group_info(services_by_group[group], entries)
        print(f"  {i}. {group:<24} {info}")
    print()
    print(_BAR)
    print("  s = sync all  |  n = normalize all  |  c = check for updates  |  q = quit")
    print(_BAR)
    print()


def _print_framework_menu(group: str, svcs: list, entries: dict, state) -> None:
    print()
    print(group)
    print("-" * 52)
    for i, svc in enumerate(svcs, 1):
        info = _svc_info(svc, entries, state)
        print(f"  {i}. {svc.label:<36} {info}")
    print()
    print(_BAR)
    print("  s = sync all  |  n = normalize  |  b = back  |  x = main menu  |  q = quit")
    print(_BAR)
    print()


# ---------------------------------------------------------------------------
# Sync / normalize actions
# ---------------------------------------------------------------------------

def _run_sync(svc, output_dir: Path, state):
    print(f"Syncing {svc.label}...", end="", flush=True)
    try:
        result = svc.runner(output_dir, dry_run=False, force=False, state=state)
        print(" done.")
        if result.downloaded:
            print(f"  Downloaded : {len(result.downloaded)}")
        if result.skipped:
            print(f"  Up to date : {len(result.skipped)}")
        if result.errors:
            print(f"  Errors     : {len(result.errors)}")
            for e in result.errors:
                print(f"    {e[0]}: {e[1]}")
        if result.manual_required:
            print(f"  Manual required: {len(result.manual_required)} (see sync report for URLs)")
        if result.notices:
            print()
            for notice in result.notices:
                print(f"  [!] {notice}")

        # Record total attempted (downloaded + skipped + errors) for X/Y display.
        # manual_required docs are not attempted by the tool so are excluded.
        total = len(result.downloaded) + len(result.skipped) + len(result.errors)
        if total > 0:
            state.set_service_total(svc.key, total)
        return result

    except Exception as exc:  # noqa: BLE001
        print(f" failed.\n  Error: {exc}")
        return None


def _run_normalize(source_dir: Path, output_dir: Path, services=None, label: str = "all") -> None:
    from core.normalizer import normalize_all

    output_dir.mkdir(parents=True, exist_ok=True)

    seen_frameworks: set[str] = set()

    def _progress(framework_key: str, filename: str) -> None:
        if framework_key not in seen_frameworks:
            seen_frameworks.add(framework_key)
            print(f"  Normalizing {framework_key}...", flush=True)

    print(f"Normalizing {label} documents...")
    print("  (This may take a while for large collections.)")
    print()

    try:
        result = normalize_all(
            source_dir, output_dir, force=False,
            progress_callback=_progress, services=services,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  Normalization failed: {exc}")
        return

    print()
    if result.processed:
        print(f"  Normalized   : {len(result.processed)}")
    if result.skipped:
        print(f"  Already done : {len(result.skipped)}")
    if result.unsupported:
        print(f"  Skipped (unsupported format) : {len(result.unsupported)}")
    if result.errors:
        print(f"  Errors       : {len(result.errors)}")
        for name, err in result.errors:
            print(f"    {name}: {err}")
    if not result.processed and not result.skipped and not result.errors:
        print("  Nothing to normalize — sync a framework first.")

    print()
    print(f"  Output: {output_dir}/")


# ---------------------------------------------------------------------------
# Quick scan
# ---------------------------------------------------------------------------

QUICK_SCAN_KEYS = ["cisa-kev", "fedramp-github", "nsa", "owasp-asvs"]


def _run_scan(source_dir: Path, state) -> None:
    from core.downloaders import SERVICES_BY_KEY

    print("Quick scan — checking for updates...")
    print()
    entries = state.entries()

    for key in QUICK_SCAN_KEYS:
        svc = SERVICES_BY_KEY[key]
        prefix = svc.subdir + "/"
        svc_entries = {k: v for k, v in entries.items() if k.startswith(prefix)}
        last = max(e["recorded_at"] for e in svc_entries.values())[:10] if svc_entries else None

        label = svc.label
        print(f"  Checking {label}...", end="", flush=True)
        try:
            result = svc.runner(source_dir, dry_run=True, force=False, state=state)
        except Exception as exc:  # noqa: BLE001
            print(f"\r  {label:<40} unable to check  ({exc})")
            continue

        if result.manual_required:
            status = f"{len(result.manual_required)} docs require manual download"
        elif result.downloaded:
            status = f"{len(result.downloaded)} update(s) available"
        else:
            n = len(result.skipped)
            status = f"up to date  ({n} file{'s' if n != 1 else ''})"

        synced = f"  last synced {last}" if last else "  never synced"
        print(f"\r  {label:<40} {status}{synced}")

    print()
    print("  Note: NIST Drafts excluded from quick scan (requires full crawl — use Sync to update).")  # noqa: E501
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _check_dependencies()

    # Lazy imports — only reached if dependencies are present
    from core.downloaders import GROUPS, SERVICES, SERVICES_BY_GROUP
    from core.reporter import build_report, save_report, slugify
    from core.state import StateFile

    source_dir = Path("source-content")
    report_dir = Path("reports")
    normalized_dir = Path("normalized-content")
    source_dir.mkdir(parents=True, exist_ok=True)
    state = StateFile(source_dir)

    while True:
        _print_group_menu(GROUPS, SERVICES_BY_GROUP, state.entries())

        try:
            choice = input("Select: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if choice in ("q", "0"):
            print("Goodbye.")
            break

        if choice == "s":
            sync_results = []
            for svc in SERVICES:
                sync_results.append((svc, _run_sync(svc, source_dir, state)))
            screen_text, full_md = build_report(sync_results, "Complete Sync")
            report_path = save_report(full_md, report_dir, "complete")
            print()
            print(screen_text)
            print(f"  Report saved: {report_path}")
            print()

        elif choice == "n":
            _run_normalize(source_dir, normalized_dir)

        elif choice == "c":
            _run_scan(source_dir, state)

        elif choice.isdigit() and 1 <= int(choice) <= len(GROUPS):
            group = GROUPS[int(choice) - 1]
            svcs  = SERVICES_BY_GROUP[group]

            while True:
                _print_framework_menu(group, svcs, state.entries(), state)

                try:
                    sub = input("Select: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    print()
                    break

                if sub in ("b", "x", "0"):
                    break

                if sub == "q":
                    print("Goodbye.")
                    sys.exit(0)

                if sub == "s":
                    sync_results = []
                    for svc in svcs:
                        sync_results.append((svc, _run_sync(svc, source_dir, state)))
                    screen_text, full_md = build_report(sync_results, f"{group} Sync")
                    report_path = save_report(full_md, report_dir, slugify(group))
                    print()
                    print(screen_text)
                    print(f"  Report saved: {report_path}")
                    print()

                elif sub == "n":
                    _run_normalize(source_dir, normalized_dir, services=svcs, label=group)

                elif sub.isdigit() and 1 <= int(sub) <= len(svcs):
                    _run_sync(svcs[int(sub) - 1], source_dir, state)

                else:
                    print("Invalid selection.")

        else:
            print("Invalid selection.")
