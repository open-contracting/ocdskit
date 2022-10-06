from ocdskit.__main__ import main
from tests import assert_streaming


def test_command(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['split-record-packages', '1'],
                     ['realdata/record-package_package.json'], ['realdata/record-package_split.json'])
