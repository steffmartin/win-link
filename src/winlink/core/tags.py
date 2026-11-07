"""Persistent tags associated with a specific link identity."""

import json
import os
from pathlib import Path
from typing import TypedDict

from winlink.core.config import get_appdata_path
from winlink.core.models import Junction
from winlink.utils.logger import get_logger

logger = get_logger(__name__)


class TagRecord(TypedDict):
    identity: str
    target: str
    tags: list[str]


def parse_tags(value: str) -> list[str]:
    """Split comma-separated tags, trimming whitespace and removing duplicates."""
    tags: list[str] = []
    seen: set[str] = set()
    for candidate in value.split(","):
        tag = candidate.strip()
        key = tag.casefold()
        if tag and key not in seen:
            tags.append(tag)
            seen.add(key)
    return tags


class LinkTagManager:
    """Read and atomically update tags without following the link at its target path."""

    def __init__(self, path: Path | None = None):
        self.path = path or get_appdata_path() / "tags.json"

    @staticmethod
    def _normalized_path(path: Path) -> str:
        return os.path.normcase(os.path.normpath(str(path.absolute())))

    @classmethod
    def _identity(cls, junction: Junction) -> str:
        stat = junction.target.lstat()
        parts = (
            cls._normalized_path(junction.target),
            cls._normalized_path(junction.source),
            junction.junction_type.value,
            str(stat.st_dev),
            str(stat.st_ino),
        )
        return "|".join(parts)

    def _read(self) -> list[TagRecord]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Could not read link tags from %s: %s", self.path, exc)
            raise OSError(f"Não foi possível ler as tags dos links: {exc}") from exc
        if not isinstance(data, list):
            raise ValueError(f"Arquivo de tags inválido: {self.path}")
        records: list[TagRecord] = []
        for item in data:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("identity"), str)
                or not isinstance(item.get("target"), str)
                or not isinstance(item.get("tags"), list)
                or not all(isinstance(tag, str) for tag in item["tags"])
            ):
                raise ValueError(f"Registro de tags inválido: {self.path}")
            records.append(
                {"identity": item["identity"], "target": item["target"], "tags": item["tags"]}
            )
        return records

    def _write(self, records: list[TagRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        try:
            temporary.write_text(
                json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            temporary.replace(self.path)
        except OSError as exc:
            logger.error("Could not save link tags to %s: %s", self.path, exc)
            raise OSError(f"Não foi possível salvar as tags dos links: {exc}") from exc

    def set_tags(self, junction: Junction, tags: list[str]) -> None:
        identity = self._identity(junction)
        target = self._normalized_path(junction.target)
        records = [record for record in self._read() if record["target"] != target]
        normalized_tags = parse_tags(",".join(tags))
        if normalized_tags:
            records.append({"identity": identity, "target": target, "tags": normalized_tags})
        self._write(records)
        junction.tags = normalized_tags

    def apply_tags(self, junctions: list[Junction]) -> None:
        records = {record["identity"]: record["tags"] for record in self._read()}
        for junction in junctions:
            try:
                identity = self._identity(junction)
            except OSError:
                junction.tags = []
                continue
            junction.tags = list(records.get(identity, []))

    def remove(self, target: Path) -> None:
        normalized = self._normalized_path(target)
        records = [record for record in self._read() if record["target"] != normalized]
        self._write(records)
