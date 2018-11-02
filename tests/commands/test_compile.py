import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('realdata/release-package-1.json', 'rb') + read('realdata/release-package-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', '--ascii', 'compile'])
        main()

    assert actual.getvalue() == read('realdata/compiled-release-1.json') + read('realdata/compiled-release-2.json')


def test_command_versioned(monkeypatch):
    stdin = read('realdata/release-package-1.json', 'rb') + read('realdata/release-package-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', '--ascii', 'compile', '--versioned'])
        main()

    assert actual.getvalue() == read('realdata/versioned-release-1.json') + read('realdata/versioned-release-2.json')


def test_command_package(monkeypatch, caplog):
    stdin = read('realdata/release-package-1.json', 'rb') + read('realdata/release-package-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'compile', '--package'])
        main()

    assert actual.getvalue() == read('realdata/record-package_package.json')


def test_command_help(monkeypatch, caplog):
    stdin = read('release-package_minimal.json', 'rb')

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', '--help'])
            main()

    assert actual.getvalue().startswith('usage: ocdskit [-h] ')

    assert len(caplog.records) == 0
    assert excinfo.value.code == 0


def test_command_pretty(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', '--pretty', 'compile'])
        main()

    assert actual.getvalue() == read('compile_pretty_minimal.json')


def test_command_encoding(monkeypatch):
    stdin = read('realdata/release-package_encoding-iso-8859-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', '--encoding', 'iso-8859-1', '--ascii', 'compile'])
        main()

    assert actual.getvalue() == read('realdata/compile_encoding_encoding.json')


def test_command_bad_encoding_iso_8859_1(monkeypatch, caplog):
    stdin = read('realdata/release-package_encoding-iso-8859-1.json', 'rb')

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'compile'])
            main()

    assert actual.getvalue() == ''

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == "encoding error: 'utf-8' codec can't decode byte 0xd3 in position 592: " \
                                        "invalid continuation byte\nTry `--encoding iso-8859-1`?"
    assert excinfo.value.code == 1


def test_command_bad_format(monkeypatch, caplog):
    stdin = b'{\n}'

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'compile'])
            main()

    assert actual.getvalue() == ''

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == "JSON error: Expecting property name enclosed in double quotes: line 2 " \
                                        "column 1 (char 2)\nIs the JSON data not line-delimited? Try piping it " \
                                        "through `jq -crM .`"
    assert excinfo.value.code == 1
