from pathlib import Path
from types import SimpleNamespace

from winlink.core.models import Junction, JunctionType
from winlink.core.tags import LinkTagManager, parse_tags


def test_parse_tags_trims_empty_values_and_case_insensitive_duplicates():
    assert parse_tags(" minha-pasta, , minhas-fotos, MINHA-PASTA ") == [
        "minha-pasta",
        "minhas-fotos",
    ]


def test_link_tags_survive_manager_reload_and_do_not_follow_reused_path(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    target = tmp_path / "link.txt"
    replacement_source = tmp_path / "replacement.txt"
    source.write_text("first")
    target.write_text("link")
    replacement_source.write_text("second")
    store = tmp_path / "tags.json"
    manager = LinkTagManager(store)
    original = Junction(
        source=source,
        target=target,
        junction_type=JunctionType.SYMLINK,
        is_directory=False,
    )
    manager.set_tags(original, ["photos", "work"])

    restarted = LinkTagManager(store)
    restored = original.model_copy()
    restarted.apply_tags([restored])
    assert restored.tags == ["photos", "work"]

    replacement = Junction(
        source=replacement_source,
        target=target,
        junction_type=JunctionType.SYMLINK,
        is_directory=False,
    )
    restarted.apply_tags([replacement])
    assert replacement.tags == []


def test_link_tag_identity_uses_link_lstat_identity(tmp_path, monkeypatch):
    target = tmp_path / "same-path"
    source = tmp_path / "source"
    junction = Junction(source=source, target=target, junction_type=JunctionType.JUNCTION)
    values = iter(
        [
            SimpleNamespace(st_dev=1, st_ino=10),
            SimpleNamespace(st_dev=1, st_ino=11),
        ]
    )
    monkeypatch.setattr(Path, "lstat", lambda self: next(values))
    manager = LinkTagManager(tmp_path / "tags.json")
    first_identity = manager._identity(junction)
    second_identity = manager._identity(junction)
    assert first_identity != second_identity
