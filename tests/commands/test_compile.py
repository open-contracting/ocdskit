import json
import logging

import pytest

import ocdskit.combine
from ocdskit.cli.__main__ import main
from ocdskit.util import json_dumps
from tests import assert_streaming, assert_streaming_error, read, run_streaming


def _remove_package_metadata(filenames):
    outputs = []
    for filename in filenames:
        data = json.loads(read(filename))
        data['publisher'] = {}
        del data['packages']
        outputs.append(data)
    return json_dumps(data) + '\n'


# Test with packages and with releases.
def assert_compile_command(capsys, monkeypatch, main, args, stdin, expected, remove_package_metadata=False):
    assert_streaming(capsys, monkeypatch, main, args, stdin, expected)

    args[args.index('compile') + 1:0] = ['--root-path', 'releases.item']
    if remove_package_metadata:
        expected = _remove_package_metadata(expected)
    assert_streaming(capsys, monkeypatch, main, args, stdin, expected)


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command(capsys, monkeypatch):
    assert_compile_command(capsys, monkeypatch, main, ['--ascii', 'compile'],
                           ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                           ['realdata/compiled-release-1.json', 'realdata/compiled-release-2.json'])


@pytest.mark.usefixtures('sqlite')
def test_command_extensions_with_packages(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['compile'],
                     ['release-package_additional-contact-points.json'], ['compile_extensions.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_extensions_with_releases(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['compile', '--root-path', 'releases.item'],
                     ['release-package_additional-contact-points.json'], ['compile_no-extensions.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_versioned(capsys, monkeypatch):
    assert_compile_command(capsys, monkeypatch, main, ['--ascii', 'compile', '--versioned'],
                           ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                           ['realdata/versioned-release-1.json', 'realdata/versioned-release-2.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package(capsys, monkeypatch):
    assert_compile_command(capsys, monkeypatch, main, ['compile', '--package'],
                           ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                           ['realdata/record-package_package.json'], remove_package_metadata=True)


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_uri_published_date_version(capsys, monkeypatch):
    actual = run_streaming(capsys, monkeypatch, main, ['compile', '--package', '--uri', 'http://example.com/x.json',
                                                       '--published-date', '2010-01-01T00:00:00Z', '--version', 'X'],
                           ['release-package_minimal.json'])

    package = json.loads(actual.out)
    assert package['uri'] == 'http://example.com/x.json'
    assert package['publishedDate'] == '2010-01-01T00:00:00Z'
    assert package['version'] == 'X'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_publisher(capsys, monkeypatch):
    actual = run_streaming(capsys, monkeypatch, main, ['compile', '--package', '--publisher-name', 'Acme Inc.',
                                                       '--publisher-uri', 'http://example.com/', '--publisher-scheme',
                                                       'scheme', '--publisher-uid', '12345'],
                           ['release-package_minimal.json'])

    package = json.loads(actual.out)
    assert package['publisher']['name'] == 'Acme Inc.'
    assert package['publisher']['uri'] == 'http://example.com/'
    assert package['publisher']['scheme'] == 'scheme'
    assert package['publisher']['uid'] == '12345'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_fake(capsys, monkeypatch):
    actual = run_streaming(capsys, monkeypatch, main, ['compile', '--package', '--fake'],
                           ['release-package_minimal.json'])

    package = json.loads(actual.out)
    assert package['uri'] == 'placeholder:'
    assert package['publishedDate'] == '9999-01-01T00:00:00Z'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_packages(capsys, monkeypatch):
    actual = run_streaming(capsys, monkeypatch, main, ['compile', '--package'],
                           ['release_minimal.json'])

    package = json.loads(actual.out)
    assert 'packages' not in package


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_linked_releases_with_packages(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['compile', '--package', '--linked-releases'],
                     ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                     ['realdata/record-package_linked-releases.json'])


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_linked_releases_with_releases(capsys, monkeypatch):
    assert_streaming(capsys, monkeypatch, main, ['compile', '--package', '--linked-releases', '--root-path',
                                                 'releases.item'],
                     ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                     _remove_package_metadata(['realdata/record-package_package.json']))


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_package_versioned(capsys, monkeypatch):
    assert_compile_command(capsys, monkeypatch, main, ['compile', '--package', '--versioned'],
                           ['realdata/release-package-1.json', 'realdata/release-package-2.json'],
                           ['realdata/record-package_versioned.json'], remove_package_metadata=True)


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_version_mismatch(capsys, monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        assert_streaming_error(capsys, monkeypatch, main, ['compile', '--package', '--versioned'],
                               ['realdata/release-package_1.1-1.json', 'realdata/release-package_1.0-1.json'])

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message == "item 1: version error: this item uses version 1.0, but earlier items " \
            "used version 1.1\nTry first upgrading items to the same version:\n  cat file [file ...] | ocdskit " \
            "upgrade 1.0:1.1 | ocdskit compile --package --versioned"


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_missing_ocid(capsys, monkeypatch, caplog):
    stdin = b'{"id":"1","date":"2001-02-03T04:05:06Z","tag":["planning"],"initiationType":"tender"}'

    with caplog.at_level(logging.ERROR):
        assert_streaming_error(capsys, monkeypatch, main, ['compile'], stdin)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message == 'The `ocid` field of at least one release is missing.'


@pytest.mark.vcr()
@pytest.mark.usefixtures('sqlite')
def test_command_unknown_version(capsys, monkeypatch, caplog):
    with caplog.at_level(logging.ERROR):
        assert_streaming_error(capsys, monkeypatch, main, ['compile'], ['release-package_unknown-version.json'])

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'CRITICAL'
        assert caplog.records[0].message == 'The `version` value ("X") of a release package is not recognized.'


@pytest.mark.vcr()
def test_command_without_sqlite(capsys, monkeypatch, caplog):
    ocdskit.combine.sqlite = False

    # To check the warning, not the output.
    run_streaming(capsys, monkeypatch, main, ['compile'], ['release-package_minimal.json'])

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == 'sqlite3 is unavailable, so the command will run in memory. If input files ' \
                                        'are too large, the command might exceed available memory.'
