import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release-schema.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet'])
        main()

    assert actual.getvalue() == read('mapping-sheet.csv').replace('\n', '\r\n')  # not sure why


def test_command_order_by(monkeypatch):
    stdin = read('release-schema.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet', '--order-by', 'path'])
        main()

    assert actual.getvalue() == read('mapping-sheet_order-by.csv').replace('\n', '\r\n')


def test_command_order_by_nonexistent(monkeypatch, caplog):
    stdin = read('release-schema.json', 'rb')

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet', '--order-by', 'nonexistent'])
            main()

    assert actual.getvalue() == ''
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == "the column 'nonexistent' doesn't exist – did you make a typo?"
    assert excinfo.value.code == 1
