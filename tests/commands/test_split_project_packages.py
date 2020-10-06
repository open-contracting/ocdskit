from ocdskit.cli.__main__ import main
from tests import assert_streaming


def test_command(monkeypatch):
    assert_streaming(monkeypatch, main, ['split-project-packages', '1'], ['oc4ids/project_package.json'],
                     ['oc4ids/project_package_split.json'])
