"""Cache management for junction scan results"""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from winlink.core.models import Junction, ScanResult
from winlink.utils.logger import get_logger

logger = get_logger(__name__)


class CacheEntry(BaseModel):
    """Single cache entry for a junction"""

    junction: Junction = Field(description="Junction data")
    cached_at: datetime = Field(
        default_factory=datetime.now, description="When this entry was cached"
    )


class JunctionCache(BaseModel):
    """Cache of junction scan results"""

    entries: list[CacheEntry] = Field(default_factory=list, description="Cached junctions")
    scan_directories: list[str] = Field(
        default_factory=list, description="Directories that were scanned"
    )
    partial: bool = False
    excluded_directories: list[str] = Field(default_factory=list)
    cached_at: datetime = Field(default_factory=datetime.now, description="When cache was created")
    version: str = Field(default="1.0", description="Cache format version")

    def to_junctions(self) -> list[Junction]:
        """Convert cache entries to list of Junction objects"""
        return [entry.junction for entry in self.entries]


class CacheManager:
    """Manager for junction cache"""

    def __init__(self, cache_path: Path | None = None):
        """
        Initialize cache manager.

        Args:
            cache_path: Path to cache file. If None, uses default location.
        """
        if cache_path is None:
            # Use APPDATA/WinLink/cache.json
            from winlink.core.config import get_appdata_path

            cache_path = get_appdata_path() / "cache.json"

        self.cache_path = cache_path
        self._cache: JunctionCache | None = None

    def load(self) -> JunctionCache | None:
        """
        Load cache from disk.

        Returns:
            JunctionCache if successful, None otherwise
        """
        self._cache = None
        if not self.cache_path.exists():
            logger.debug(f"Cache file not found: {self.cache_path}")
            return None

        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)

            self._cache = JunctionCache(**data)
            if self._cache.version != "1.0":
                self._cache = None
                return None
            logger.info(
                f"Loaded cache with {len(self._cache.entries)} entries from {self._cache.cached_at}"
            )
            return self._cache
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def save(
        self, scan_result: ScanResult, *, requested_directories: list[Path] | None = None
    ) -> bool:
        """
        Save scan result to cache.

        Args:
            scan_result: Scan result to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            directories = [
                str(path)
                for path in (
                    scan_result.scanned_directories
                    if requested_directories is None
                    else requested_directories
                )
            ]
            exclusions = [str(path) for path in scan_result.excluded_directories]
            entries: dict[Path, CacheEntry] = {}
            if scan_result.cancelled:
                if not scan_result.junctions:
                    return True
                previous = self.load()
                if (
                    previous
                    and previous.scan_directories == directories
                    and previous.excluded_directories == exclusions
                ):
                    entries.update((entry.junction.target, entry) for entry in previous.entries)
            entries.update(
                (junction.target, CacheEntry(junction=junction))
                for junction in scan_result.junctions
            )

            cache = JunctionCache(
                entries=list(entries.values()),
                scan_directories=directories,
                excluded_directories=exclusions,
                partial=scan_result.cancelled,
                cached_at=datetime.now(),
            )

            # Ensure parent directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            temporary = self.cache_path.with_suffix(".tmp")
            with open(temporary, "w", encoding="utf-8") as f:
                f.write(cache.model_dump_json(indent=2))

            temporary.replace(self.cache_path)
            self._cache = cache
            logger.info(f"Saved cache with {len(entries)} entries to {self.cache_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear cache file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
                self._cache = None
                logger.info("Cache cleared")
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_cache_age_seconds(self) -> float | None:
        """
        Get age of cache in seconds.

        Returns:
            Age in seconds if cache exists, None otherwise
        """
        if self._cache is None:
            self.load()

        if self._cache is None:
            return None

        return (datetime.now(self._cache.cached_at.tzinfo) - self._cache.cached_at).total_seconds()

    def is_cache_valid(self, max_age_seconds: float = 3600) -> bool:
        """
        Check if cache is valid (not too old).

        Args:
            max_age_seconds: Maximum age in seconds for cache to be considered valid

        Returns:
            True if cache is valid, False otherwise
        """
        age = self.get_cache_age_seconds()
        if age is None:
            return False

        return max_age_seconds > 0 and 0 <= age < max_age_seconds

    def get_cached_junctions(self) -> list[Junction]:
        """
        Get cached junctions.

        Returns:
            List of cached junctions, or empty list if no cache
        """
        if self._cache is None:
            self.load()

        if self._cache is None:
            return []

        return self._cache.to_junctions()
