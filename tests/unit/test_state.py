"""Unit tests for compligator.state."""

import json
from pathlib import Path

import pytest

from compligator.state import StateFile


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.mark.unit
def test_empty_state_has_no_entries(state_dir: Path) -> None:
    state = StateFile(state_dir)
    assert state.entries() == {}


@pytest.mark.unit
def test_record_and_retrieve(state_dir: Path) -> None:
    state = StateFile(state_dir)
    dest = state_dir / "test.pdf"
    dest.write_bytes(b"fake pdf content")
    state.record(dest, "https://example.com/test.pdf")

    entries = state.entries()
    assert "test.pdf" in entries
    assert entries["test.pdf"]["url"] == "https://example.com/test.pdf"


@pytest.mark.unit
def test_is_fresh_after_record(state_dir: Path) -> None:
    state = StateFile(state_dir)
    dest = state_dir / "test.pdf"
    dest.write_bytes(b"fake pdf content")
    state.record(dest, "https://example.com/test.pdf")

    assert state.is_fresh(dest, "https://example.com/test.pdf") is True


@pytest.mark.unit
def test_is_fresh_missing_file(state_dir: Path) -> None:
    state = StateFile(state_dir)
    dest = state_dir / "missing.pdf"
    assert state.is_fresh(dest, "https://example.com/missing.pdf") is False


@pytest.mark.unit
def test_needs_adopt_for_untracked_file(state_dir: Path) -> None:
    state = StateFile(state_dir)
    dest = state_dir / "orphan.pdf"
    dest.write_bytes(b"some bytes")
    assert state.needs_adopt(dest) is True


@pytest.mark.unit
def test_adopt_removes_needs_adopt(state_dir: Path) -> None:
    state = StateFile(state_dir)
    dest = state_dir / "orphan.pdf"
    dest.write_bytes(b"some bytes")
    state.adopt(dest, "https://example.com/orphan.pdf")
    assert state.needs_adopt(dest) is False


@pytest.mark.unit
def test_service_total_roundtrip(state_dir: Path) -> None:
    state = StateFile(state_dir)
    state.set_service_total("fedramp", 42)
    assert state.get_service_total("fedramp") == 42


@pytest.mark.unit
def test_state_persists_across_instances(state_dir: Path) -> None:
    state1 = StateFile(state_dir)
    dest = state_dir / "persist.pdf"
    dest.write_bytes(b"data")
    state1.record(dest, "https://example.com/persist.pdf")

    state2 = StateFile(state_dir)
    assert "persist.pdf" in state2.entries()


@pytest.mark.unit
def test_unknown_service_total_returns_zero(state_dir: Path) -> None:
    state = StateFile(state_dir)
    assert state.get_service_total("nonexistent") == 0
