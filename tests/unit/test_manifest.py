"""Unit tests for compligator.manifest."""

import json
import os
import time
from pathlib import Path

import pytest

from compligator.manifest import (
    Manifest,
    FrameworkEntry,
    _CACHE_TTL_HOURS,
    _SCHEMA_VERSION,
    _parse,
    _load_bundled,
    load_manifest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_RAW: dict = {
    "schema_version": _SCHEMA_VERSION,
    "updated": "2026-04-17",
    "frameworks": {
        "fedramp-github": {"dynamic": True},
        "nist-privacy": {"total": 1, "automated": 1, "manual": 0},
        "pci-dss": {"total": 9, "automated": 7, "manual": 2},
    },
}


# ---------------------------------------------------------------------------
# _parse()
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_parse_valid_returns_manifest() -> None:
    manifest = _parse(_VALID_RAW)
    assert isinstance(manifest, Manifest)
    assert manifest.schema_version == _SCHEMA_VERSION
    assert manifest.updated == "2026-04-17"


@pytest.mark.unit
def test_parse_wrong_schema_version_raises() -> None:
    bad = {**_VALID_RAW, "schema_version": _SCHEMA_VERSION + 1}
    with pytest.raises(ValueError, match="schema_version"):
        _parse(bad)


@pytest.mark.unit
def test_parse_dynamic_entry() -> None:
    manifest = _parse(_VALID_RAW)
    entry = manifest.get("fedramp-github")
    assert entry is not None
    assert entry.dynamic is True
    assert entry.total is None
    assert entry.automated is None
    assert entry.manual is None


@pytest.mark.unit
def test_parse_fixed_entry() -> None:
    manifest = _parse(_VALID_RAW)
    entry = manifest.get("nist-privacy")
    assert entry is not None
    assert entry.dynamic is False
    assert entry.total == 1
    assert entry.automated == 1
    assert entry.manual == 0


@pytest.mark.unit
def test_parse_mixed_entry() -> None:
    manifest = _parse(_VALID_RAW)
    entry = manifest.get("pci-dss")
    assert entry is not None
    assert entry.total == 9
    assert entry.automated == 7
    assert entry.manual == 2


@pytest.mark.unit
def test_manifest_get_missing_key_returns_none() -> None:
    manifest = _parse(_VALID_RAW)
    assert manifest.get("no-such-framework") is None


# ---------------------------------------------------------------------------
# _load_bundled()
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_load_bundled_returns_manifest() -> None:
    manifest = _load_bundled()
    assert isinstance(manifest, Manifest)
    assert manifest.schema_version == _SCHEMA_VERSION


@pytest.mark.unit
def test_bundled_manifest_has_known_frameworks() -> None:
    manifest = _load_bundled()
    # Spot-check a fixed entry and a dynamic entry
    fixed = manifest.get("nist-privacy")
    assert fixed is not None and not fixed.dynamic and fixed.total == 1

    dynamic = manifest.get("nist-finals")
    assert dynamic is not None and dynamic.dynamic is True


@pytest.mark.unit
def test_bundled_manifest_covers_all_services() -> None:
    from compligator.downloaders import SERVICES

    manifest = _load_bundled()
    missing = [s.key for s in SERVICES if manifest.get(s.key) is None]
    assert missing == [], f"Service keys missing from manifest: {missing}"


# ---------------------------------------------------------------------------
# load_manifest() — cache behaviour (no network needed)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_load_manifest_returns_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("compligator.manifest._CACHE_FILE", tmp_path / "cache.json")
    monkeypatch.setattr("compligator.manifest._CACHE_DIR", tmp_path)
    # Patch remote fetch to always fail so we fall through to bundled
    monkeypatch.setattr("compligator.manifest._fetch_remote", lambda: None)

    manifest = load_manifest()
    assert isinstance(manifest, Manifest)


@pytest.mark.unit
def test_load_manifest_uses_valid_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(_VALID_RAW), encoding="utf-8")

    monkeypatch.setattr("compligator.manifest._CACHE_FILE", cache_file)
    monkeypatch.setattr("compligator.manifest._CACHE_DIR", tmp_path)
    monkeypatch.setattr("compligator.manifest._fetch_remote", lambda: None)

    manifest = load_manifest()
    assert manifest.updated == "2026-04-17"


@pytest.mark.unit
def test_load_manifest_ignores_stale_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(_VALID_RAW), encoding="utf-8")
    # Back-date the file modification time past the TTL
    stale_mtime = time.time() - (_CACHE_TTL_HOURS + 1) * 3600
    os.utime(cache_file, (stale_mtime, stale_mtime))

    monkeypatch.setattr("compligator.manifest._CACHE_FILE", cache_file)
    monkeypatch.setattr("compligator.manifest._CACHE_DIR", tmp_path)
    monkeypatch.setattr("compligator.manifest._fetch_remote", lambda: None)

    # Falls through to bundled (which has different updated value)
    manifest = load_manifest()
    bundled = _load_bundled()
    assert manifest.updated == bundled.updated


@pytest.mark.unit
def test_load_manifest_ignores_wrong_schema_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad_cache = {**_VALID_RAW, "schema_version": _SCHEMA_VERSION + 99}
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(bad_cache), encoding="utf-8")

    monkeypatch.setattr("compligator.manifest._CACHE_FILE", cache_file)
    monkeypatch.setattr("compligator.manifest._CACHE_DIR", tmp_path)
    monkeypatch.setattr("compligator.manifest._fetch_remote", lambda: None)

    manifest = load_manifest()
    assert manifest.schema_version == _SCHEMA_VERSION
