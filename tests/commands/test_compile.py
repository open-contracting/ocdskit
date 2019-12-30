import json
import logging
import re
import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

import ocdskit.combine
from ocdskit.cli.__main__ import main
from tests import assert_command, read, run_command, assert_command_error


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command(monkeypatch):
    assert_command(monkeypatch, main, ['--ascii', 'compile'],
                   ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                   ['realdata/compiled-release-1.json', 'realdata/compiled-release-2.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_extensions(monkeypatch):
    assert_command(monkeypatch, main, ['compile'],
                   ['release-package_additional-contact-points.json'],
                   ['compile_extensions.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_versioned(monkeypatch):
    assert_command(monkeypatch, main, ['--ascii', 'compile', '--versioned'],
                   ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                   ['realdata/versioned-release-1.json', 'realdata/versioned-release-2.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package(monkeypatch):
    assert_command(monkeypatch, main, ['compile', '--package'],
                   ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                   ['realdata/record-package_package.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_uri_published_date(monkeypatch):
    actual = run_command(monkeypatch, main, ['compile', '--package', '--uri', 'http://example.com/x.json',
                                             '--published-date', '2010-01-01T00:00:00Z'],
                                            ['release-package_minimal.json'])

    package = json.loads(actual)
    assert package['uri'] == 'http://example.com/x.json'
    assert package['publishedDate'] == '2010-01-01T00:00:00Z'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_publisher(monkeypatch):
    actual = run_command(monkeypatch, main, ['compile', '--package', '--publisher-name', 'Acme Inc.',
                                             '--publisher-uri', 'http://example.com/', '--publisher-scheme', 'scheme',
                                             '--publisher-uid', '12345'],
                                            ['release-package_minimal.json'])

    package = json.loads(actual)
    assert package['publisher']['name'] == 'Acme Inc.'
    assert package['publisher']['uri'] == 'http://example.com/'
    assert package['publisher']['scheme'] == 'scheme'
    assert package['publisher']['uid'] == '12345'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_fake(monkeypatch):
    actual = run_command(monkeypatch, main, ['compile', '--package', '--fake'], ['release-package_minimal.json'])

    package = json.loads(actual)
    assert package['uri'] == 'placeholder:'
    assert package['publishedDate'] == '9999-01-01T00:00:00Z'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_linked_releases(monkeypatch):
    assert_command(monkeypatch, main, ['compile', '--package', '--linked-releases'],
                   ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                   ['realdata/record-package_linked-releases.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_versioned(monkeypatch):
    assert_command(monkeypatch, main, ['compile', '--package', '--versioned'],
                   ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                   ['realdata/record-package_versioned.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_version_mismatch(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        assert_command_error(monkeypatch, main, ['compile', '--package', '--versioned'],
                             ['realdata/release-package_1.1-1.json', 'realdata/release-package_1.0-1.json'])

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message == "item 1: version error: this item uses version 1.0, but earlier items " \
            "used version 1.1\nTry first upgrading items to the same version:\n  cat file [file ...] | ocdskit " \
            "upgrade 1.0:1.1 | ocdskit compile --package --versioned"


@pytest.mark.usefixtures('sqlite')
def test_command_help(monkeypatch, caplog):
    stdin = read('release-package_minimal.json', 'rb')

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', '--help'])
            main()

    assert actual.getvalue().startswith('usage: ocdskit [-h] ')

    assert len(caplog.records) == 0
    assert excinfo.value.code == 0


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_pretty(monkeypatch):
    assert_command(monkeypatch, main, ['--pretty', 'compile'],
                   ['release-package_minimal.json'],
                   ['compile_pretty_minimal.json'])


@pytest.mark.usefixtures('sqlite')
def test_command_encoding(monkeypatch):
    assert_command(monkeypatch, main, ['--encoding', 'iso-8859-1', '--ascii', 'compile'],
                   ['realdata/release-package_encoding-iso-8859-1.json'],
                   ['realdata/compile_encoding_encoding.json'])


@pytest.mark.usefixtures('sqlite')
def test_command_bad_encoding_iso_8859_1(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        assert_command_error(monkeypatch, main, ['compile'],
                             ['realdata/release-package_encoding-iso-8859-1.json'])

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert re.search(r"^encoding error: (?:'utf-8' codec can't decode byte 0xd3 in position \d+: invalid "
                         r"continuation byte)?\nTry `--encoding iso-8859-1`\?$", caplog.records[0].message)


@pytest.mark.usefixtures('sqlite')
def test_command_multiline_input(monkeypatch):
    stdin = b'{\n  "releases": [\n    {\n      "ocid": "x",\n      "date": "2001-02-03T00:00:00Z"\n    }\n  ]\n}'

    actual = run_command(monkeypatch, main, ['compile'], stdin)

    assert actual == '{"tag":["compiled"],"id":"x-2001-02-03T00:00:00Z","date":"2001-02-03T00:00:00Z","ocid":"x"}\n'  # noqa: E501


@pytest.mark.usefixtures('sqlite')
def test_command_array_input(monkeypatch):
    actual = run_command(monkeypatch, main, ['compile'], ['release-packages.json'])

    assert actual == '{"tag":["compiled"],"id":"ocds-213czf-1-2001-02-03T04:05:06Z","date":"2001-02-03T04:05:06Z","ocid":"ocds-213czf-1","initiationType":"tender"}\n'  # noqa: E501


@pytest.mark.usefixtures('sqlite')
def test_command_invalid_json(monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        stdin = read('release-package_minimal.json', 'rb') + b'\n{\n'

        assert_command_error(monkeypatch, main, ['compile'], stdin)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message.startswith('JSON error: ')


@pytest.mark.vcr()
def test_command_without_sqlite(monkeypatch, caplog):
    ocdskit.combine.sqlite = False

    run_command(monkeypatch, main, ['--pretty', 'compile'],
                ['release-package_minimal.json'])

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == 'sqlite3 is unavailable, so the command will run in memory. If input files ' \
                                        'are too large, the command might exceed available memory.'
