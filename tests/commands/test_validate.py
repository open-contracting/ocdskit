import os
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
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate'])
        main()

    assert actual.getvalue() == "item 0: 'version' is a required property (required)\n"


@pytest.mark.vcr()
def test_command_invalid_json(monkeypatch, caplog):
    with caplog.at_level('INFO'):
        stdin = read('release-package_minimal.json', 'rb') + b'\n{\n'

        with pytest.raises(SystemExit) as excinfo:
            with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:  # noqa
                monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate'])
                main()

        assert actual.getvalue() == ''

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message.startswith('JSON error: ')
        assert excinfo.value.code == 1


@pytest.mark.vcr()
def test_command_valid_release_package_url(monkeypatch):
    url = 'http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json'

    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert actual.getvalue() == ''


@pytest.mark.vcr()
def test_command_valid_release_package_file(monkeypatch):
    url = 'file://{}'.format(os.path.realpath(os.path.join('tests', 'fixtures', 'release-package-schema.json')))

    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert actual.getvalue() == ''


@pytest.mark.vcr()
def test_command_valid_release_package_file_verbose(monkeypatch):
    url = 'file://{}'.format(os.path.realpath(os.path.join('tests', 'fixtures', 'release-package-schema.json')))

    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url, '--verbose'])
        main()

    assert actual.getvalue() == 'item 0: no errors\n'


@pytest.mark.vcr()
def test_command_invalid_record_package(monkeypatch):
    url = 'https://standard.open-contracting.org/latest/en/record-package-schema.json'

    stdin = read('realdata/record-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert "item 0: None is not of type 'string' (properties/records/items/properties/compiledRelease/properties/tender/properties/submissionMethod/items/type)" in actual.getvalue()  # noqa


@pytest.mark.vcr()
def test_command_no_check_urls(monkeypatch):
    stdin = read('release-package_urls.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate'])
        main()

    assert actual.getvalue() == ''


def test_command_check_urls(monkeypatch):
    stdin = read('release-package_urls.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--check-urls', '--timeout', '3'])
        main()

    assert actual.getvalue() == """HTTP 500 on GET http://httpbin.org/status/500
item 0: 'http://httpbin.org/status/500' is not a 'uri' (properties/releases/items/properties/tender/properties/documents/items/properties/url/format)
Timedout on GET http://httpbin.org/delay/3
item 0: 'http://httpbin.org/delay/3' is not a 'uri' (properties/releases/items/properties/tender/properties/documents/items/properties/url/format)
"""  # noqa
