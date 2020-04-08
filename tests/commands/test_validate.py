import logging
import os.path

import pytest

from ocdskit.cli.__main__ import main
from tests import assert_streaming_error, read, run_streaming


@pytest.mark.vcr()
def test_command(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['validate'],
                           ['realdata/release-package-1.json'])

    assert actual == "item 0: 'version' is a required property (required)\n"


@pytest.mark.vcr()
def test_command_invalid_json(monkeypatch, caplog):
    with caplog.at_level(logging.INFO):
        stdin = read('release-package_minimal.json', 'rb') + b'\n{\n'

        assert_streaming_error(monkeypatch, main, ['validate'], stdin)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message.startswith('JSON error: ')


@pytest.mark.vcr()
def test_command_valid_release_package_url(monkeypatch):
    url = 'http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json'

    actual = run_streaming(monkeypatch, main, ['validate', '--schema', url],
                           ['realdata/release-package-1.json'])

    assert actual == ''


@pytest.mark.vcr()
def test_command_valid_release_package_file(monkeypatch):
    url = 'file://{}'.format(os.path.realpath(os.path.join('tests', 'fixtures', 'release-package-schema.json')))

    actual = run_streaming(monkeypatch, main, ['validate', '--schema', url],
                           ['realdata/release-package-1.json'])

    assert actual == ''


@pytest.mark.vcr()
def test_command_valid_release_package_file_verbose(monkeypatch):
    url = 'file://{}'.format(os.path.realpath(os.path.join('tests', 'fixtures', 'release-package-schema.json')))

    actual = run_streaming(monkeypatch, main, ['validate', '--schema', url, '--verbose'],
                           ['realdata/release-package-1.json'])

    assert actual == 'item 0: no errors\n'


@pytest.mark.vcr()
def test_command_invalid_record_package(monkeypatch):
    url = 'https://standard.open-contracting.org/latest/en/record-package-schema.json'

    actual = run_streaming(monkeypatch, main, ['validate', '--schema', url],
                           ['realdata/record-package-1.json'])

    assert "item 0: None is not of type 'string' (properties/records/items/properties/compiledRelease/properties/tender/properties/submissionMethod/items/type)" in actual  # noqa: E501


@pytest.mark.vcr()
def test_command_no_check_urls(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['validate'],
                           ['release-package_urls.json'])

    assert actual == ''


@pytest.mark.vcr()
def test_command_check_urls(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['validate', '--check-urls'],
                           ['release-package_url-error.json'])

    assert actual == """HTTP 500 on GET http://httpbin.org/status/500
item 0: 'http://httpbin.org/status/500' is not a 'uri' (properties/releases/items/properties/tender/properties/documents/items/properties/url/format)
"""  # noqa: E501


# Can't record delay endpoint with VCR.
def test_command_timeout(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['validate', '--check-urls', '--timeout', '1'],
                           ['release-package_url-timeout.json'])

    assert actual == """Timedout on GET http://httpbin.org/delay/3
item 0: 'http://httpbin.org/delay/3' is not a 'uri' (properties/releases/items/properties/tender/properties/documents/items/properties/url/format)
"""  # noqa: E501
