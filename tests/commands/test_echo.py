import logging
import re
import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import assert_streaming, assert_streaming_error, read, run_streaming


@patch('sys.stdout', new_callable=StringIO)
def test_help(stdout, monkeypatch, caplog):
    stdin = read('release-package_minimal.json', 'rb')

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
            monkeypatch.setattr(sys, 'argv', ['ocdskit', '--help'])
            main()

    assert stdout.getvalue().startswith('usage: ocdskit [-h] ')

    assert len(caplog.records) == 0
    assert excinfo.value.code == 0


def test_command_encoding(monkeypatch):
    assert_streaming(monkeypatch, main, ['--encoding', 'iso-8859-1', 'echo'],
                     ['realdata/release-package_encoding-iso-8859-1.json'],
                     ['realdata/release-package_encoding-utf-8.json'])


def test_command_bad_encoding_iso_8859_1(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        assert_streaming_error(monkeypatch, main, ['echo'],
                               ['realdata/release-package_encoding-iso-8859-1.json'])

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        # macOS and Linux have different error messages.
        assert re.search(r"^encoding error: (?:'utf-8' codec can't decode byte 0xd3 in position \d+: invalid "
                         r"continuation byte|lexical error: invalid bytes in UTF8 string.(\n[^\n]+){2}\n)\n"
                         r"Try `--encoding iso-8859-1`\?$", caplog.records[0].message)


def test_command_ascii(monkeypatch):
    assert_streaming(monkeypatch, main, ['--ascii', 'echo'],
                     ['encoding_utf-8.json'], ['encoding_ascii.json'])


def test_command_utf_8(monkeypatch):
    assert_streaming(monkeypatch, main, ['echo'],
                     ['encoding_ascii.json'], ['encoding_utf-8.json'])


def test_command_pretty(monkeypatch):
    assert_streaming(monkeypatch, main, ['--pretty', 'echo'],
                     ['release_minimal.json'], ['release_minimal_pretty.json'])


def test_command_compact(monkeypatch):
    assert_streaming(monkeypatch, main, ['echo'],
                     ['release_minimal_pretty.json'], ['release_minimal.json'])


def test_command_multiline_input(monkeypatch):
    stdin = b'{\n  "releases": [\n    {\n      "ocid": "x",\n      "date": "2001-02-03T00:00:00Z"\n    }\n  ]\n}'

    actual = run_streaming(monkeypatch, main, ['echo'], stdin)

    assert actual == '{"releases":[{"ocid":"x","date":"2001-02-03T00:00:00Z"}]}\n'


def test_command_array_input(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['echo'], ['release-packages.json'])

    assert actual == (
        '{"uri":"http://example.com/id/1","publisher":{"name":"Acme"},"publishedDate":"2001-02-03T04:05:07Z","releases":[{"ocid":"ocds-213czf-1","id":"1","date":"2001-02-03T04:05:06Z","tag":["planning"],"initiationType":"tender"}],"version":"1.1"}\n'  # noqa: E501
        '{"uri":"http://example.com/id/1","publisher":{"name":"Acme"},"publishedDate":"2001-02-03T04:05:07Z","releases":[{"ocid":"ocds-213czf-1","id":"1","date":"2001-02-03T04:05:06Z","tag":["planning"],"initiationType":"tender"}],"version":"1.1"}\n'  # noqa: E501
    )


def test_command_invalid_json(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        stdin = read('release-package_minimal.json', 'rb') + b'\n{\n'

        assert_streaming_error(monkeypatch, main, ['echo'], stdin, expected=read('release-package_minimal.json'))

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message.startswith('JSON error: ')
