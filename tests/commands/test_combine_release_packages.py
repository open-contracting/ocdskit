import json
import sys
from io import BytesIO, TextIOWrapper
from unittest.mock import patch

import pytest

from ocdskit.__main__ import main
from tests import assert_streaming, read, run_streaming


def test_command(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['combine-release-packages'],
                     ['release-package_minimal.json', 'release-package_maximal.json',
                      'release-package_extensions.json'],
                     ['combine-release-packages_minimal-maximal-extensions.json'])


def test_command_no_extensions(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['combine-release-packages'],
                     ['release-package_minimal.json'],
                     ['combine-release-packages_minimal.json'])


def test_command_uri_published_date(capsys, monkeypatch):
    actual = run_streaming(capsys, monkeypatch, main, ['combine-release-packages', '--uri',
                                                       'http://example.com/x.json', '--published-date',
                                                       '2010-01-01T00:00:00Z', '--version', '1.2'],
                           ['release-package_minimal.json'])

    package = json.loads(actual.out)
    assert package['uri'] == 'http://example.com/x.json'
    assert package['publishedDate'] == '2010-01-01T00:00:00Z'
    assert package['version'] == '1.2'


def test_command_publisher(capsys, monkeypatch):
    actual = run_streaming(capsys, monkeypatch, main, ['combine-release-packages', '--publisher-name', 'Acme Inc.'],
                           ['release-package_minimal.json'])

    package = json.loads(actual.out)
    assert package['publisher']['name'] == 'Acme Inc.'


@pytest.mark.filterwarnings("default::ocdskit.exceptions.MissingReleasesWarning")
def test_command_missing_field(capsys, monkeypatch):
    stdin = read('record-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'combine-release-packages'])
        main()

    captured = capsys.readouterr()

    assert captured.out == '{"uri":"","publisher":{"name":"Acme"},"publishedDate":"","version":"1.1","releases":[]}\n'  # noqa: E501
    assert captured.err == 'item 0 has no "releases" field (check that it is a release package)\n'
