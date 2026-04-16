"""Shared terminal UI helpers for CompliGator."""

from __future__ import annotations

WIDTH = 70
BAR = "─" * WIDTH


def visual_len(s: str) -> int:
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
    """Print a padded label: status line aligned to width."""
    label_part = f"  {label}: "
    padding = width - len(label_part) - visual_len(status)
    if padding < 0:
        padding = 0
    print(label_part + " " * padding + status)
