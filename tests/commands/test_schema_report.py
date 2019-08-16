import sys
from io import StringIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import path


def test_command(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'schema-report', '--min-occurrences', '2',
                                          path('test-schema.json')])
        main()

    assert actual.getvalue() == '''codelist,openCodelist
a.csv,False/True
b.csv,False
c.csv,False
d.csv,False

 2: {'codelist': 'a.csv', 'openCodelist': True, 'type': ['string', 'null']}
'''


def test_command_no_codelists(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'schema-report', '--min-occurrences', '2', '--no-codelists',
                                          path('test-schema.json')])
        main()

    assert 'codelist,openCodelist' not in actual.getvalue()
    assert ':' in actual.getvalue()


def test_command_no_definitions(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'schema-report', '--min-occurrences', '2', '--no-definitions',
                                          path('test-schema.json')])
        main()

    assert 'codelist,openCodelist' in actual.getvalue()
    assert ':' not in actual.getvalue()


def test_command_min_occurrences(monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'schema-report', '--min-occurrences', '1', '--no-codelists',
                                          path('test-schema.json')])
        main()

    assert 'codelist,openCodelist' not in actual.getvalue()
    assert '1:' in actual.getvalue()
