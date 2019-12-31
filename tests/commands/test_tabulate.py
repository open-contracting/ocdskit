import pytest

from ocdskit.cli.__main__ import main
from tests import run_streaming


@pytest.mark.vcr()
def test_command(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['tabulate', 'sqlite://'], ['realdata/release-package-1.json'])

    assert actual == ''


@pytest.mark.vcr()
def test_command_release_package(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['tabulate', 'sqlite://'], ['release-package_minimal.json'])

    assert actual == ''


@pytest.mark.vcr()
def test_command_record_package(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['tabulate', 'sqlite://'], ['record-package_minimal.json'])

    assert actual == ''


@pytest.mark.vcr()
def test_command_drop(monkeypatch, tmpdir):
    stdin = ['release-package_minimal.json']
    database_url = 'sqlite:///{}'.format(tmpdir.join('tmp.db'))

    run_streaming(monkeypatch, main, ['tabulate', database_url], stdin)
    actual = run_streaming(monkeypatch, main, ['tabulate', database_url, '--drop'], stdin)

    assert actual == ''
