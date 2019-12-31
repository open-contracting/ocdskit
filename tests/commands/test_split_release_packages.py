from ocdskit.cli.__main__ import main
from tests import assert_streaming


def test_command(monkeypatch):
    assert_streaming(monkeypatch, main, ['split-release-packages', '2'], ['realdata/release-package-1-2.json'],
                     ['realdata/release-package_split.json'])
