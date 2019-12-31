from ocdskit.cli.__main__ import main
from tests import path, run_command


def test_command(monkeypatch):
    actual = run_command(monkeypatch, main, ['schema-report', '--min-occurrences', '2',
                                             path('test-schema.json')])

    assert actual == 'codelist,openCodelist\n' \
                     'a.csv,False/True\n' \
                     'b.csv,False\n' \
                     'c.csv,False\n' \
                     'd.csv,False\n' \
                     '\n' \
                     " 2: {'codelist': 'a.csv', 'openCodelist': True, 'type': ['string', 'null']}\n"


def test_command_no_codelists(monkeypatch):
    actual = run_command(monkeypatch, main, ['schema-report', '--min-occurrences', '2', '--no-codelists',
                                             path('test-schema.json')])

    assert 'codelist,openCodelist' not in actual
    assert ':' in actual


def test_command_no_definitions(monkeypatch):
    actual = run_command(monkeypatch, main, ['schema-report', '--min-occurrences', '2', '--no-definitions',
                                             path('test-schema.json')])

    assert 'codelist,openCodelist' in actual
    assert ':' not in actual


def test_command_min_occurrences(monkeypatch):
    actual = run_command(monkeypatch, main, ['schema-report', '--min-occurrences', '1', '--no-codelists',
                                             path('test-schema.json')])

    assert 'codelist,openCodelist' not in actual
    assert '1:' in actual
