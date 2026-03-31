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
# Visual helpers
# ---------------------------------------------------------------------------

WIDTH = 70
_BAR = "─" * WIDTH


def _visual_len(s: str) -> int:
    """Return terminal column width, counting emoji/wide chars as 2 columns."""
    count = 0
    for ch in s:
        cp = ord(ch)
        if 0xFE00 <= cp <= 0xFE0F or cp == 0x200D:
            continue
        if cp >= 0x2600 and not (0x2500 <= cp <= 0x257F):
            count += 2
        else:
            count += 1
    return count


def _print_box(title: str) -> None:
    """Print a centred title inside a ╔═══╗ box."""
    print("╔" + "═" * (WIDTH - 2) + "╗")
    inner = WIDTH - 2
    padding = (inner - len(title)) // 2
    right = inner - padding - len(title)
    print("║" + " " * padding + title + " " * right + "║")
    print("╚" + "═" * (WIDTH - 2) + "╝")


def _print_section(title: str) -> None:
    """Print a ─── section divider with a label."""
    print()
    print(_BAR)
    print(title)
    print(_BAR)


def _status_icon(entries: dict, svc) -> str:
    """Return a status icon for a service based on acquisition mode and sync state."""
    if svc.acquisition == "manual":
        return "[M]"
    if svc.acquisition == "mixed":
        return "[~]"
    prefix = svc.subdir + "/"
    if any(k.startswith(prefix) for k in entries):
        return "[x]"
    return "[ ]"


def _split_by_acquisition(svcs: list) -> list:
    """Return services ordered: auto first (preserving order), then mixed/manual."""
    auto = [s for s in svcs if s.acquisition == "auto"]
    non_auto = [s for s in svcs if s.acquisition != "auto"]
    return auto + non_auto


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


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
    _print_box("COMPLIGATOR")
    print()
    print(_BAR)
    print("MAIN MENU")
    print(_BAR)
    print(f"  {'[0]':<6} Configure")
    for i, group in enumerate(groups, 1):
        info = _group_info(services_by_group[group], entries)
        print(f"  [{i}]{'':3} {group:<24} {info}")
    print()
    print(_BAR)
    print("  s = sync all  |  n = normalize all  |  c = check for updates  |  q = quit")
    print(_BAR)
    print()


def _print_framework_menu(group: str, svcs: list, entries: dict, state) -> None:
    """Print the framework sub-menu. svcs must be pre-ordered (auto first, then mixed/manual)."""
    print()
    print(_BAR)
    print(group)
    print(_BAR)

    has_non_auto = any(s.acquisition != "auto" for s in svcs)
    in_manual_section = False

    for i, svc in enumerate(svcs, 1):
        if has_non_auto and not in_manual_section and svc.acquisition != "auto":
            print()
            label = "── Partial / Manual Acquisition "
            print(f"  {label}{'─' * (WIDTH - 2 - len(label))}")
            in_manual_section = True

        icon = _status_icon(entries, svc)
        info = _svc_info(svc, entries, state)
        print(f"  {icon} [{i}]  {svc.label:<36} {info}")

    print()
    print(_BAR)
    print("  [x] synced  [ ] not synced  [~] partial  [M] manual only")
    print(_BAR)
    print("  s = sync all  |  n = normalize  |  b = back  |  x = main menu  |  q = quit")
    print(_BAR)
    print()


# ---------------------------------------------------------------------------
# Sync / normalize actions
# ---------------------------------------------------------------------------

def _run_sync(svc, output_dir: Path, state):
    print(f"  Syncing {svc.label}...", end="", flush=True)
    try:
        result = svc.runner(output_dir, dry_run=False, force=False, state=state)

        downloaded = len(result.downloaded)
        skipped    = len(result.skipped)
        errors     = len(result.errors)
        manual     = len(result.manual_required)

        parts = []
        if downloaded:
            parts.append(f"{downloaded} new")
        if skipped:
            parts.append(f"{skipped} up-to-date")
        if errors:
            parts.append(f"{errors} error(s)")
        if manual:
            parts.append(f"{manual} manual")
        summary = "  ".join(parts) if parts else "nothing to do"
        print(f" done  [{summary}]")

        if result.errors:
            for e in result.errors:
                print(f"      error: {e[0]}: {e[1]}")
        if result.manual_required:
            print(f"      {manual} doc(s) require manual download (see sync report for URLs)")
        if result.notices:
            print()
            for notice in result.notices:
                print(f"      [!] {notice}")

        total = downloaded + skipped + errors + manual
        if total > 0:
            state.set_service_total(svc.key, total)
        return result

    except Exception as exc:  # noqa: BLE001
        print(f" failed\n      Error: {exc}")
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
    print("  Note: NIST Drafts excluded from quick scan (requires full crawl — use Sync).")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _check_dependencies()

    # Lazy imports — only reached if dependencies are present
    from core.configure import active_service_keys, load_config, run_configure
    from core.downloaders import GROUPS, SERVICES
    from core.reporter import build_report, save_report, slugify
    from core.state import StateFile

    source_dir     = Path("source-content")
    report_dir     = Path("reports")
    normalized_dir = Path("normalized-content")
    source_dir.mkdir(parents=True, exist_ok=True)
    state = StateFile(source_dir)

    # Load config and apply tracked-framework filter
    cfg = load_config()
    all_keys = [s.key for s in SERVICES]
    active_keys = active_service_keys(cfg, all_keys)
    active_svcs = [s for s in SERVICES if s.key in active_keys]

    # Rebuild group-aware structures from filtered service list
    active_groups = [g for g in GROUPS if any(s.group == g for s in active_svcs)]
    active_by_group = {g: [s for s in active_svcs if s.group == g] for g in active_groups}

    # Auto-check on launch (if configured)
    if cfg.get("auto_check_on_launch"):
        _run_scan(source_dir, state)

    while True:
        entries = state.entries()
        _print_group_menu(active_groups, active_by_group, entries)

        try:
            choice = input("Select: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye.")
            break

        if choice in ("q", ):
            print("Goodbye.")
            break

        if choice == "0":
            cfg = run_configure(SERVICES)
            # Re-apply tracked-framework filter after configure
            active_keys = active_service_keys(cfg, all_keys)
            active_svcs = [s for s in SERVICES if s.key in active_keys]
            active_groups = [g for g in GROUPS if any(s.group == g for s in active_svcs)]
            active_by_group = {g: [s for s in active_svcs if s.group == g] for g in active_groups}
            continue

        if choice == "s":
            print()
            sync_results = []
            for svc in active_svcs:
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

        elif choice.isdigit() and 1 <= int(choice) <= len(active_groups):
            group = active_groups[int(choice) - 1]
            svcs  = _split_by_acquisition(active_by_group[group])

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
                    print()
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
                    print()
                    _run_sync(svcs[int(sub) - 1], source_dir, state)
                    print()

                else:
                    print("  Invalid selection.")

        else:
            print("  Invalid selection.")
