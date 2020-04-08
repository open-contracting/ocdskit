import os.path
from tempfile import TemporaryDirectory

import pytest

from ocdskit.cli.__main__ import main
from tests import assert_command, path, run_command

test_command_argvalues = [
    ('record-package_minimal.json', 'record package'),
    ('release-package_minimal.json', 'release package'),
    ('record_minimal.json', 'record'),
    ('release_minimal.json', 'release'),
    ('realdata/compiled-release-1.json', 'compiled release'),
    ('realdata/versioned-release-1.json', 'versioned release'),
    ('release-packages.json', 'a JSON array of release packages'),
    ('release-packages.jsonl', 'concatenated JSON, starting with a JSON array of release packages'),
    ('detect-format_mixed.json', 'concatenated JSON, starting with release'),
    ('detect-format_whitespace.json', 'release'),
]

test_command_unknown_format_argvalues = [
    ('false', 'boolean'),
    ('null', 'null'),
    ('number', 'number'),
    ('string', 'string'),
    ('true', 'boolean'),
    ('array', 'non-OCDS array'),
    ('object', 'non-OCDS object'),
]

content = b'{"records":[]}'


@pytest.mark.parametrize('filename,result', test_command_argvalues)
def test_command(filename, result, monkeypatch):
    expected = 'tests/fixtures/{}: {}\n'.format(filename, result)
    assert_command(monkeypatch, main, ['detect-format', path(filename)], expected)


def test_command_recursive(monkeypatch, caplog):
    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'test.json'), 'wb') as f:
            f.write(content)

        with open(os.path.join(d, '.test.json'), 'wb') as f:
            f.write(content)

        actual = run_command(monkeypatch, main, ['detect-format', '--recursive', d])

        assert '/test.json: record package' in actual
        assert '.test.json' not in actual
        assert len(caplog.records) == 0


@pytest.mark.parametrize('basename,result', test_command_unknown_format_argvalues)
def test_command_unknown_format(basename, result, monkeypatch, caplog):
    filename = 'detect-format_{}.json'.format(basename)

    assert_command(monkeypatch, main, ['detect-format', path(filename)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == 'tests/fixtures/{}: unknown (top-level JSON value is a {})'.format(
        filename, result)


def test_command_directory(monkeypatch, caplog):
    with TemporaryDirectory() as d:
        assert_command(monkeypatch, main, ['detect-format', d], '')

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'WARNING'
        assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(monkeypatch, caplog):
    assert_command(monkeypatch, main, ['detect-format', 'nonexistent'], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'
