"""CompliGator configuration module.

Provides a settings dashboard accessible from [0] Configure in the main menu.
Configuration is persisted to .compligator-config.json in the working directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Version (kept in sync with pyproject.toml)
# ---------------------------------------------------------------------------

VERSION = "0.3.2-beta"

# ---------------------------------------------------------------------------
# Visual helpers
# ---------------------------------------------------------------------------

WIDTH = 70


def _visual_len(s: str) -> int:
    """Return terminal column width, counting emoji/wide chars as 2 columns."""
    count = 0
    for ch in s:
        cp = ord(ch)
        # Skip zero-width variation selectors and zero-width joiners
        if 0xFE00 <= cp <= 0xFE0F or cp == 0x200D:
            continue
        # Wide emoji/symbols: anything >= U+2600 except box-drawing (U+2500–U+257F)
        if cp >= 0x2600 and not (0x2500 <= cp <= 0x257F):
            count += 2
        else:
            count += 1
    return count


def print_box(title: str, width: int = WIDTH) -> None:
    """Print a centred title inside a ╔═══╗ box."""
    print("╔" + "═" * (width - 2) + "╗")
    inner = width - 2
    padding = (inner - len(title)) // 2
    right = inner - padding - len(title)
    print("║" + " " * padding + title + " " * right + "║")
    print("╚" + "═" * (width - 2) + "╝")


def print_section(title: str, width: int = WIDTH) -> None:
    """Print a ─── section divider with a label."""
    print()
    print("─" * width)
    print(title)
    print("─" * width)


def print_status_line(label: str, status: str, width: int = WIDTH) -> None:
    """Print a ║ label: status ║ line with right-aligned ║."""
    label_part = f"  {label}: "
    status_part = f"{status}"
    padding = width - len(label_part) - _visual_len(status_part)
    if padding < 0:
        padding = 0
    print(label_part + " " * padding + status_part)


# ---------------------------------------------------------------------------
# Config file
# ---------------------------------------------------------------------------

CONFIG_FILENAME = ".compligator-config.json"

DEFAULT_CONFIG: dict = {
    "auto_check_on_launch": False,
    "tracked_frameworks": None,   # None = all frameworks enabled
}


def get_config_path(cwd: Optional[Path] = None) -> Path:
    return (cwd or Path.cwd()) / CONFIG_FILENAME


def load_config(cwd: Optional[Path] = None) -> dict:
    """Load config from disk, merging with defaults for any missing keys."""
    path = get_config_path(cwd)
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict, cwd: Optional[Path] = None) -> None:
    path = get_config_path(cwd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Tracked-framework helpers
# ---------------------------------------------------------------------------


def active_service_keys(cfg: dict, all_keys: list[str]) -> list[str]:
    """Return the list of framework keys that are currently enabled."""
    tracked = cfg.get("tracked_frameworks")
    if tracked is None:
        return all_keys
    return [k for k in all_keys if k in tracked]


# ---------------------------------------------------------------------------
# Configure dashboard
# ---------------------------------------------------------------------------


def _print_configure_header(cfg: dict, total_services: int) -> None:
    print_box("COMPLIGATOR — CONFIGURE", WIDTH)
    print()

    auto = "Enabled" if cfg.get("auto_check_on_launch") else "Disabled"
    tracked = cfg.get("tracked_frameworks")
    if tracked is None:
        fw_status = f"All ({total_services})"
    else:
        n = len([k for k in tracked])
        fw_status = f"{n} of {total_services}"

    print_status_line("Version                  ", VERSION)
    print_status_line("Auto-check on launch     ", auto)
    print_status_line("Tracked frameworks       ", fw_status)
    print()


def _print_configure_menu() -> None:
    print("─" * WIDTH)
    print("SETTINGS")
    print("─" * WIDTH)
    print("  [1] Toggle auto-check on launch")
    print("  [2] Manage tracked frameworks")
    print()
    print("─" * WIDTH)
    print("  b = back to main menu  |  q = quit")
    print("─" * WIDTH)
    print()


# ---------------------------------------------------------------------------
# Settings actions
# ---------------------------------------------------------------------------


def _toggle_auto_check(cfg: dict, cwd: Optional[Path] = None) -> None:
    cfg["auto_check_on_launch"] = not cfg.get("auto_check_on_launch", False)
    state = "Enabled" if cfg["auto_check_on_launch"] else "Disabled"
    save_config(cfg, cwd)
    print(f"  Auto-check on launch: {state}")
    print()


def _manage_frameworks(cfg: dict, all_services: list, cwd: Optional[Path] = None) -> None:
    """Interactive menu to opt frameworks in or out."""
    all_keys = [s.key for s in all_services]
    tracked = cfg.get("tracked_frameworks")
    # None means all enabled — convert to explicit list for editing
    if tracked is None:
        enabled: set[str] = set(all_keys)
    else:
        enabled = set(tracked)

    while True:
        print()
        print("─" * WIDTH)
        print("TRACKED FRAMEWORKS  (toggle on/off — syncs only enabled frameworks)")
        print("─" * WIDTH)

        # Group by service group
        from core.downloaders import GROUPS
        for group in GROUPS:
            print(f"  {group}")
            for i, svc in enumerate(all_services):
                if svc.group != group:
                    continue
                icon = "[x]" if svc.key in enabled else "[ ]"
                idx = all_keys.index(svc.key) + 1
                print(f"    {icon} {idx:>2}. {svc.label}")

        print()
        print("─" * WIDTH)
        print("  Enter number to toggle  |  a = enable all  |  n = disable all")
        print("  s = save and return  |  b = cancel (discard changes)  |  q = quit")
        print("─" * WIDTH)
        print()

        try:
            choice = input("Select: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice in ("b",):
            break
        if choice == "q":
            print("Goodbye.")
            sys.exit(0)
        if choice == "a":
            enabled = set(all_keys)
        elif choice == "n":
            enabled = set()
        elif choice == "s":
            # None = all enabled (canonical form)
            if enabled == set(all_keys):
                cfg["tracked_frameworks"] = None
            else:
                cfg["tracked_frameworks"] = [k for k in all_keys if k in enabled]
            save_config(cfg, cwd)
            print("  Tracked frameworks saved.")
            print()
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(all_keys):
            key = all_keys[int(choice) - 1]
            if key in enabled:
                enabled.discard(key)
            else:
                enabled.add(key)
        else:
            print("  Invalid selection.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_configure(all_services: list, cwd: Optional[Path] = None) -> dict:
    """Show the configure dashboard. Returns the (possibly updated) config."""
    cfg = load_config(cwd)
    total = len(all_services)

    while True:
        _print_configure_header(cfg, total)
        _print_configure_menu()

        try:
            choice = input("Select: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if choice in ("b", "0"):
            break
        if choice == "q":
            print("Goodbye.")
            sys.exit(0)
        if choice == "1":
            _toggle_auto_check(cfg, cwd)
        elif choice == "2":
            _manage_frameworks(cfg, all_services, cwd)
        else:
            print("  Invalid selection.")

    return cfg
