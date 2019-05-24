import sys
from io import StringIO
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import path, read


def test_command(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet', '--infer-required', path('release-schema.json')])
        main()

    assert actual.getvalue() == read('mapping-sheet.csv').replace('\n', '\r\n')  # not sure why


def test_command_order_by(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet', '--order-by', 'path',
                                          '--infer-required', path('release-schema.json')])
        main()

    assert actual.getvalue() == read('mapping-sheet_order-by.csv').replace('\n', '\r\n')


def test_command_person_statement(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet', '--order-by', 'path',
                                          '--infer-required', path('bods/person-statement.json')])
        main()

    assert actual.getvalue() == read('mapping-sheet_person-statement.csv').replace('\n', '\r\n')


def test_command_order_by_nonexistent(monkeypatch, caplog):
    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'mapping-sheet', '--order-by', 'nonexistent',
                                              path('release-schema.json')])
            main()

    assert actual.getvalue() == ''
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == "the column 'nonexistent' doesn't exist – did you make a typo?"
    assert excinfo.value.code == 1
