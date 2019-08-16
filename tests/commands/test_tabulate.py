import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import read


@pytest.mark.vcr()
def test_command(monkeypatch):
    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'tabulate', 'sqlite://'])
        main()

    assert actual.getvalue() == ''


@pytest.mark.vcr()
def test_command_release_package(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'tabulate', 'sqlite://'])
        main()

    assert actual.getvalue() == ''


@pytest.mark.vcr()
def test_command_record_package(monkeypatch):
    stdin = read('record-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'tabulate', 'sqlite://', '--drop'])
        main()

    assert actual.getvalue() == ''


@pytest.mark.vcr()
def test_command_drop(monkeypatch, tmpdir):
    stdin = read('release-package_minimal.json', 'rb')

    database_url = 'sqlite:///{}'.format(tmpdir.join('tmp.db'))

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'tabulate', database_url])
        main()

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'tabulate', database_url, '--drop'])
        main()

    assert actual.getvalue() == ''
