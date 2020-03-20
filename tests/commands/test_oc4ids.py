from ocdskit.cli.__main__ import main
from tests import assert_streaming


def test_command(monkeypatch):
    assert_streaming(monkeypatch, main, ['convert-to-oc4ids', '--project-id', '1'],
                     ['release_1.1.json'],
                     ['oc4ids-project_minimal.json'])
