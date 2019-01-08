import sys
from io import StringIO, TextIOWrapper, BytesIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command_record(monkeypatch):
    stdin = read('realdata/record-package-1.0.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/record-package-1.1.json')


def test_command_release_1(monkeypatch):
    stdin = read('realdata/release-package-1.0-1.json', 'rb')  # has tender, buyer, awards

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/release-package-1.1-1.json')


def test_command_release_2(monkeypatch):
    stdin = read('realdata/release-package-1.0-2.json', 'rb')  # has transactions

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/release-package-1.1-2.json')
