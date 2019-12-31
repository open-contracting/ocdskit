import json

from ocdskit.cli.__main__ import main
from tests import assert_streaming, run_streaming


def test_command(monkeypatch):
    assert_streaming(monkeypatch, main, ['combine-release-packages'],
                     ['release-package_minimal.json', 'release-package_maximal.json',
                      'release-package_extensions.json'],
                     ['combine-release-packages_minimal-maximal-extensions.json'])


def test_command_no_extensions(monkeypatch):
    assert_streaming(monkeypatch, main, ['combine-release-packages'],
                     ['release-package_minimal.json'],
                     ['combine-release-packages_minimal.json'])


def test_command_uri_published_date(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['combine-release-packages', '--uri', 'http://example.com/x.json',
                                               '--published-date', '2010-01-01T00:00:00Z'],
                           ['release-package_minimal.json'])

    package = json.loads(actual)
    assert package['uri'] == 'http://example.com/x.json'
    assert package['publishedDate'] == '2010-01-01T00:00:00Z'


def test_command_publisher(monkeypatch):
    actual = run_streaming(monkeypatch, main, ['combine-release-packages', '--publisher-name', 'Acme Inc.'],
                           ['release-package_minimal.json'])

    package = json.loads(actual)
    assert package['publisher']['name'] == 'Acme Inc.'
