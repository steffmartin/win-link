"""Keep tests independent of the user's application data."""

import pytest


@pytest.fixture(autouse=True)
def isolated_application_data(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
