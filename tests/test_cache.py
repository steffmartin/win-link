"""Tests for junction cache management"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from winlink.core.cache import CacheEntry, CacheManager, JunctionCache
from winlink.core.models import Junction, JunctionStatus, JunctionType, ScanResult


def test_cache_entry_creation():
    """Test creating a cache entry"""
    junction = Junction(
        source=Path("D:/source"),
        target=Path("C:/target"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
    )

    entry = CacheEntry(junction=junction)

    assert entry.junction == junction
    assert entry.cached_at is not None


def test_junction_cache_creation():
    """Test creating a junction cache"""
    junction1 = Junction(
        source=Path("D:/source1"),
        target=Path("C:/target1"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
    )

    junction2 = Junction(
        source=Path("D:/source2"),
        target=Path("C:/target2"),
        junction_type=JunctionType.SYMLINK,
        status=JunctionStatus.ACTIVE,
    )

    entries = [CacheEntry(junction=junction1), CacheEntry(junction=junction2)]

    cache = JunctionCache(
        entries=entries,
        scan_directories=["C:/Users/test", "D:/Cache"],
    )

    assert len(cache.entries) == 2
    assert len(cache.scan_directories) == 2
    assert cache.version == "1.0"


def test_junction_cache_to_junctions():
    """Test converting cache to junctions list"""
    junction1 = Junction(
        source=Path("D:/source1"),
        target=Path("C:/target1"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
    )

    junction2 = Junction(
        source=Path("D:/source2"),
        target=Path("C:/target2"),
        junction_type=JunctionType.SYMLINK,
        status=JunctionStatus.ACTIVE,
    )

    entries = [CacheEntry(junction=junction1), CacheEntry(junction=junction2)]
    cache = JunctionCache(entries=entries)

    junctions = cache.to_junctions()

    assert len(junctions) == 2
    assert junctions[0] == junction1
    assert junctions[1] == junction2


def test_cache_manager_save_and_load():
    """Test saving and loading cache"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.json"
        manager = CacheManager(cache_path)

        # Create scan result
        from winlink.core.models import ScanResult

        junction = Junction(
            source=Path("D:/source"),
            target=Path("C:/target"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
        )

        scan_result = ScanResult(
            junctions=[junction],
            scanned_directories=[Path("C:/Users/test")],
            scan_duration_seconds=1.5,
        )

        # Save cache
        assert manager.save(scan_result) is True
        assert cache_path.exists()

        # Load cache
        loaded_cache = manager.load()
        assert loaded_cache is not None
        assert len(loaded_cache.entries) == 1
        assert loaded_cache.entries[0].junction == junction


def test_cache_manager_load_nonexistent():
    """Test loading cache when file doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "nonexistent.json"
        manager = CacheManager(cache_path)

        loaded_cache = manager.load()
        assert loaded_cache is None


def test_cache_manager_clear():
    """Test clearing cache"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.json"
        manager = CacheManager(cache_path)

        # Create and save cache
        from winlink.core.models import ScanResult

        junction = Junction(
            source=Path("D:/source"),
            target=Path("C:/target"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
        )

        scan_result = ScanResult(
            junctions=[junction],
            scanned_directories=[Path("C:/Users/test")],
            scan_duration_seconds=1.5,
        )

        manager.save(scan_result)
        assert cache_path.exists()

        # Clear cache
        assert manager.clear() is True
        assert not cache_path.exists()


def test_cache_manager_get_cache_age():
    """Test getting cache age"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.json"
        manager = CacheManager(cache_path)

        # No cache yet
        assert manager.get_cache_age_seconds() is None

        # Create and save cache
        from winlink.core.models import ScanResult

        junction = Junction(
            source=Path("D:/source"),
            target=Path("C:/target"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
        )

        scan_result = ScanResult(
            junctions=[junction],
            scanned_directories=[Path("C:/Users/test")],
            scan_duration_seconds=1.5,
        )

        manager.save(scan_result)

        # Get age
        age = manager.get_cache_age_seconds()
        assert age is not None
        assert age < 1.0  # Should be very recent


def test_cache_manager_is_cache_valid():
    """Test cache validity check"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.json"
        manager = CacheManager(cache_path)

        # No cache
        assert manager.is_cache_valid() is False

        # Create and save cache
        from winlink.core.models import ScanResult

        junction = Junction(
            source=Path("D:/source"),
            target=Path("C:/target"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
        )

        scan_result = ScanResult(
            junctions=[junction],
            scanned_directories=[Path("C:/Users/test")],
            scan_duration_seconds=1.5,
        )

        manager.save(scan_result)

        # Should be valid with default max age (1 hour)
        assert manager.is_cache_valid() is True

        # Should be invalid with 0 max age
        assert manager.is_cache_valid(max_age_seconds=0) is False


def test_cache_manager_get_cached_junctions():
    """Test getting cached junctions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.json"
        manager = CacheManager(cache_path)

        # No cache
        assert manager.get_cached_junctions() == []

        # Create and save cache
        from winlink.core.models import ScanResult

        junction1 = Junction(
            source=Path("D:/source1"),
            target=Path("C:/target1"),
            junction_type=JunctionType.JUNCTION,
            status=JunctionStatus.ACTIVE,
        )

        junction2 = Junction(
            source=Path("D:/source2"),
            target=Path("C:/target2"),
            junction_type=JunctionType.SYMLINK,
            status=JunctionStatus.ACTIVE,
        )

        scan_result = ScanResult(
            junctions=[junction1, junction2],
            scanned_directories=[Path("C:/Users/test")],
            scan_duration_seconds=1.5,
        )

        manager.save(scan_result)

        # Get cached junctions
        cached = manager.get_cached_junctions()
        assert len(cached) == 2
        assert cached[0] == junction1
        assert cached[1] == junction2


def test_cache_manager_handles_corrupt_file():
    """Test that cache manager handles corrupt cache file gracefully"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.json"
        manager = CacheManager(cache_path)

        # Write corrupt data
        cache_path.write_text("corrupt json data {{{")

        # Should return None on load
        loaded_cache = manager.load()
        assert loaded_cache is None


def test_cache_upsert_and_remove_single_junction(tmp_path):
    """Point updates must not require a full scan result."""
    manager = CacheManager(tmp_path / "cache.json")
    junction = Junction(
        source=Path("D:/source"),
        target=Path("C:/target"),
        junction_type=JunctionType.JUNCTION,
        status=JunctionStatus.ACTIVE,
    )
    other = Junction(
        source=Path("D:/other"),
        target=Path("C:/other"),
        junction_type=JunctionType.SYMLINK,
        status=JunctionStatus.BROKEN,
    )
    manager.save(
        ScanResult(junctions=[junction], scanned_directories=[Path("C:/")])
    )

    assert manager.upsert_junction(other)
    cached = {entry.junction.target: entry for entry in manager.load().entries}
    assert set(cached) == {junction.target, other.target}

    updated = junction.model_copy(update={"status": JunctionStatus.INACCESSIBLE})
    assert manager.upsert_junction(updated)
    cached = {entry.junction.target: entry for entry in manager.load().entries}
    assert cached[junction.target].junction.status == JunctionStatus.INACCESSIBLE
    assert len(cached) == 2

    assert manager.remove_junction(junction.target)
    cached = {entry.junction.target: entry for entry in manager.load().entries}
    assert set(cached) == {other.target}


def test_cache_point_update_without_cache_is_a_noop(tmp_path):
    manager = CacheManager(tmp_path / "missing.json")
    junction = Junction(
        source=Path("D:/source"),
        target=Path("C:/target"),
        junction_type=JunctionType.JUNCTION,
    )
    assert manager.upsert_junction(junction) is False
    assert manager.remove_junction(junction.target) is False
    assert not manager.cache_path.exists()
