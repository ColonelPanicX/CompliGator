"""Layer 3 — Textual TUI for CompliGator.

Launched by default from ``compligator.cli.main()`` when Textual is available.
Force the CLI menu with ``--no-tui``.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Label,
    RichLog,
    Static,
    Switch,
    Tree,
)
from textual.widgets.tree import TreeNode

from compligator.configure import active_service_keys, get_config_path, load_config
from compligator.downloaders import GROUPS, SERVICES, SERVICES_BY_GROUP, SERVICES_BY_KEY, ServiceDef
from compligator.manifest import FrameworkEntry, Manifest, load_manifest
from compligator.state import StateFile

# ---------------------------------------------------------------------------
# Status icon / label helpers
# ---------------------------------------------------------------------------

_SYNCED = "[green]✓[/green]"
_PARTIAL = "[yellow]~[/yellow]"
_UNSYNCED = "[dim]·[/dim]"
_MANUAL = "[blue]M[/blue]"
_SYNCING = "[yellow]⟳[/yellow]"

_LEGEND = (
    f"{_SYNCED} synced  "
    f"{_PARTIAL} partial / dynamic  "
    f"{_UNSYNCED} not synced  "
    f"{_MANUAL} manual only"
)


def _status_icon(on_disk: int, entry: Optional[FrameworkEntry], acquisition: str) -> str:
    if acquisition == "manual":
        return _MANUAL
    if entry is None or entry.dynamic:
        return _PARTIAL if on_disk > 0 else _UNSYNCED
    total = entry.total or 0
    if total > 0 and on_disk >= total:
        return _SYNCED
    if on_disk > 0:
        return _PARTIAL
    return _UNSYNCED


def _count_str(on_disk: int, entry: Optional[FrameworkEntry]) -> str:
    if entry is None or entry.dynamic:
        return str(on_disk) if on_disk > 0 else "—"
    return f"{on_disk}/{entry.total}"


def _make_label(
    svc: ServiceDef,
    entries: dict,
    manifest: Manifest,
    syncing: bool = False,
) -> str:
    if syncing:
        return f"{_SYNCING}  {svc.label:<44} [yellow]syncing…[/yellow]"
    prefix = svc.subdir + "/"
    on_disk = sum(1 for k in entries if k.startswith(prefix))
    m_entry = manifest.get(svc.key)
    icon = _status_icon(on_disk, m_entry, svc.acquisition)
    count = _count_str(on_disk, m_entry)
    return f"{icon}  {svc.label:<44} [dim]{count}[/dim]"


def _save_config_quietly(cfg: dict) -> None:
    """Persist config without printing (safe to call from within the TUI)."""
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)


# ---------------------------------------------------------------------------
# Settings screen
# ---------------------------------------------------------------------------


class SettingsScreen(ModalScreen[Optional[dict]]):
    """Modal overlay for framework tracking and launch preferences."""

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }
    #settings-dialog {
        width: 74;
        height: auto;
        max-height: 88%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    #settings-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    #auto-check-row {
        height: 3;
        align: left middle;
        padding-bottom: 1;
    }
    #auto-check-row Switch {
        margin-right: 1;
    }
    #fw-list-title {
        text-style: bold;
        padding: 1 0 0 0;
    }
    #fw-list {
        height: 22;
        border: round $primary-darken-2;
        padding: 0 1;
        margin-top: 1;
    }
    #settings-buttons {
        height: 3;
        align: center middle;
        padding-top: 1;
    }
    #settings-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, cfg: dict, all_svcs: list[ServiceDef]) -> None:
        super().__init__()
        self._cfg = dict(cfg)
        self._all_svcs = all_svcs

    def compose(self) -> ComposeResult:
        tracked = self._cfg.get("tracked_frameworks")  # None = all enabled

        from textual.containers import Container

        with Container(id="settings-dialog"):
            yield Label("⚙  Settings", id="settings-title")
            with Horizontal(id="auto-check-row"):
                yield Switch(
                    value=self._cfg.get("auto_check_on_launch", False),
                    id="auto-check-switch",
                )
                yield Label("Auto-check on launch")
            yield Label("Tracked Frameworks", id="fw-list-title")
            with VerticalScroll(id="fw-list"):
                for svc in self._all_svcs:
                    enabled = tracked is None or svc.key in tracked
                    safe_id = f"fw-{svc.key.replace('-', '_')}"
                    yield Checkbox(svc.label, value=enabled, id=safe_id)
            with Horizontal(id="settings-buttons"):
                yield Button("Save  [ctrl+s]", id="save-btn", variant="success")
                yield Button("Cancel  [esc]", id="cancel-btn")

    def action_dismiss_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        self._do_save()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._do_save()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def _do_save(self) -> None:
        all_keys = [s.key for s in self._all_svcs]
        enabled = []
        for svc in self._all_svcs:
            safe_id = f"#fw-{svc.key.replace('-', '_')}"
            cb = self.query_one(safe_id, Checkbox)
            if cb.value:
                enabled.append(svc.key)

        new_cfg = dict(self._cfg)
        new_cfg["auto_check_on_launch"] = self.query_one("#auto-check-switch", Switch).value
        new_cfg["tracked_frameworks"] = None if len(enabled) == len(all_keys) else enabled
        new_cfg["known_frameworks"] = all_keys
        _save_config_quietly(new_cfg)
        self.dismiss(new_cfg)


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------


class CompliGatorApp(App[None]):
    """CompliGator TUI — compliance document aggregator."""

    TITLE = "CompliGator"

    DEFAULT_CSS = """
    #main {
        height: 1fr;
    }
    #tree-panel {
        width: 3fr;
        border-right: tall $primary-darken-2;
    }
    #framework-tree {
        height: 1fr;
    }
    #legend {
        height: 1;
        padding: 0 1;
        border-top: solid $primary-darken-3;
        color: $text-muted;
    }
    #activity-log {
        width: 2fr;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("s", "sync_selected", "Sync"),
        Binding("g", "sync_group", "Sync Group"),
        Binding("A", "sync_all", "Sync All"),
        Binding("n", "normalize_selected", "Normalize"),
        Binding("c", "check_selected", "Check"),
        Binding("comma", "settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._source_dir = Path("source-content")
        self._output_dir = Path("output")
        self._normalized_dir = Path("normalized-content")
        self._source_dir.mkdir(parents=True, exist_ok=True)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._state: StateFile = StateFile(self._source_dir)
        self._manifest: Manifest = load_manifest()
        self._cfg: dict = load_config()
        self._node_map: dict[str, TreeNode] = {}
        self._syncing: set[str] = set()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="tree-panel"):
                yield Tree("Frameworks", id="framework-tree")
                yield Static(_LEGEND, id="legend")
            yield RichLog(id="activity-log", markup=True, highlight=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one("#framework-tree", Tree)
        tree.show_root = False
        self._build_tree()
        self._write_log(
            "Ready — [bold]s[/bold] sync  "
            "[bold]A[/bold] sync all  "
            "[bold]c[/bold] check  "
            "[bold],[/bold] settings  "
            "[bold]q[/bold] quit"
        )

    # ------------------------------------------------------------------
    # Tree management
    # ------------------------------------------------------------------

    def _build_tree(self) -> None:
        """Populate the framework tree from the active service list."""
        tree = self.query_one("#framework-tree", Tree)
        tree.root.remove_children()
        self._node_map = {}

        all_keys = [s.key for s in SERVICES]
        active_keys = set(active_service_keys(self._cfg, all_keys))
        entries = self._state.entries()

        for group in GROUPS:
            svcs = [s for s in SERVICES_BY_GROUP.get(group, []) if s.key in active_keys]
            if not svcs:
                continue
            group_node = tree.root.add(group, expand=True)
            for svc in svcs:
                label = _make_label(svc, entries, self._manifest)
                node = group_node.add_leaf(label, data=svc.key)
                self._node_map[svc.key] = node

        tree.root.expand()

    def _refresh_node(self, key: str) -> None:
        """Update a single node's label (must be called from the main thread)."""
        node = self._node_map.get(key)
        if node is None:
            return
        svc = SERVICES_BY_KEY.get(key)
        if svc is None:
            return
        node.label = _make_label(
            svc,
            self._state.entries(),
            self._manifest,
            syncing=key in self._syncing,
        )

    # ------------------------------------------------------------------
    # Activity log
    # ------------------------------------------------------------------

    def _write_log(self, message: str) -> None:
        log = self.query_one("#activity-log", RichLog)
        ts = datetime.now().strftime("%H:%M:%S")
        log.write(f"[dim]{ts}[/dim]  {message}")

    # ------------------------------------------------------------------
    # Sync worker
    # ------------------------------------------------------------------

    @work(thread=True, exit_on_error=False)
    def _sync_worker(self, key: str, dry_run: bool = False) -> None:
        # Show in-progress indicator immediately
        self._syncing.add(key)
        self.call_from_thread(self._refresh_node, key)

        svc = SERVICES_BY_KEY.get(key)
        if svc is None:
            self._syncing.discard(key)
            self.call_from_thread(self._write_log, f"[red]Unknown service key: {key}[/red]")
            return

        prefix = "[dim][DRY RUN][/dim] " if dry_run else ""
        self.call_from_thread(self._write_log, f"{prefix}Syncing [bold]{svc.label}[/bold]…")

        try:
            result = svc.runner(  # type: ignore[call-arg]
                self._source_dir,
                dry_run=dry_run,
                force=False,
                state=self._state,
            )

            dl = len(result.downloaded)
            sk = len(result.skipped)
            er = len(result.errors)
            mn = len(result.manual_required)
            total = dl + sk + er + mn

            if not dry_run and total > 0:
                self._state.set_service_total(key, total)

            parts = []
            if dl:
                parts.append(f"[green]{dl} new[/green]")
            if sk:
                parts.append(f"{sk} up-to-date")
            if er:
                parts.append(f"[red]{er} error(s)[/red]")
            if mn:
                parts.append(f"[yellow]{mn} manual[/yellow]")

            summary = "  ".join(parts) if parts else "nothing to do"
            self.call_from_thread(
                self._write_log,
                f"{prefix}[bold]{svc.label}[/bold]  {summary}",
            )

            if result.errors:
                for err in result.errors:
                    self.call_from_thread(self._write_log, f"  [red]✗[/red] {err[0]}: {err[1]}")

            if result.notices:
                for notice in result.notices:
                    self.call_from_thread(self._write_log, f"  [yellow]![/yellow] {notice}")

        except Exception as exc:  # noqa: BLE001
            self.call_from_thread(
                self._write_log,
                f"[red]✗ {svc.label} failed: {exc}[/red]",
            )

        finally:
            # Always restore node to normal state
            self._syncing.discard(key)
            self.call_from_thread(self._refresh_node, key)

    # ------------------------------------------------------------------
    # Key actions
    # ------------------------------------------------------------------

    def action_sync_selected(self) -> None:
        node = self.query_one("#framework-tree", Tree).cursor_node
        if node is None:
            self._write_log("[dim]Navigate to a framework first (arrow keys).[/dim]")
            return
        if node.data:
            self._sync_worker(node.data)
        else:
            # Cursor is on a group header — sync the whole group
            self.action_sync_group()

    def action_sync_group(self) -> None:
        node = self.query_one("#framework-tree", Tree).cursor_node
        if node is None:
            self._write_log("[dim]Navigate to a group first (arrow keys).[/dim]")
            return
        group_node = node.parent if node.data else node
        if group_node is None or group_node.is_root:
            self._write_log("[dim]Navigate to a framework or group first.[/dim]")
            return
        keys = [child.data for child in group_node.children if child.data]
        if not keys:
            return
        self._write_log(f"Syncing group [bold]{group_node.label}[/bold] ({len(keys)} frameworks)…")
        for key in keys:
            self._sync_worker(key)

    def action_sync_all(self) -> None:
        all_keys = [s.key for s in SERVICES]
        active_keys = active_service_keys(self._cfg, all_keys)
        self._write_log(f"Syncing all {len(active_keys)} active frameworks…")
        for key in active_keys:
            self._sync_worker(key)

    def action_check_selected(self) -> None:
        node = self.query_one("#framework-tree", Tree).cursor_node
        if node is None:
            self._write_log("[dim]Navigate to a framework first (arrow keys).[/dim]")
            return
        if node.data:
            self._sync_worker(node.data, dry_run=True)
        else:
            self._write_log("[dim]Navigate to a specific framework to check it.[/dim]")

    def action_normalize_selected(self) -> None:
        self._write_log("[yellow]Normalization will be wired in a future session.[/yellow]")

    def action_settings(self) -> None:
        all_svcs = list(SERVICES)

        def _on_settings_close(new_cfg: Optional[dict]) -> None:
            if new_cfg is not None:
                self._cfg = new_cfg
                self._write_log("Settings saved — rebuilding framework list…")
                self._build_tree()

        self.push_screen(SettingsScreen(self._cfg, all_svcs), callback=_on_settings_close)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    CompliGatorApp().run()
