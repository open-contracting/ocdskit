from ocdskit.cli.__main__ import main
from tests import assert_streaming


def test_command(monkeypatch):
    assert_streaming(monkeypatch, main, ['split-record-packages', '1'], ['realdata/record-package_package.json'],
                     ['realdata/record-package_split.json'])
