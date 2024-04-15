import os

import pytest

from ocdskit.__main__ import main
from tests import assert_command, assert_command_error, path, run_command


@pytest.mark.parametrize('filename,result', [
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
    ('detect-format_empty.json', ('empty package')),
])
def test_command(filename, result, capsys, monkeypatch):
    expected = f'tests{os.sep}fixtures{os.sep}{filename}: {result}\n'
    assert_command(capsys, monkeypatch, main, ['detect-format', path(filename)], expected)


@pytest.mark.parametrize('filename,root_path,result', [
    ('record-package_minimal.json', 'records', 'a JSON array of records'),
    ('record-package_minimal.json', 'records.item', 'record'),
])
def test_command_root_path(filename, root_path, result, capsys, monkeypatch):
    expected = f'tests{os.sep}fixtures{os.sep}{filename}: {result}\n'
    assert_command(capsys, monkeypatch, main, ['detect-format', '--root-path', root_path, path(filename)], expected)


def test_command_root_path_nonexistent(capsys, monkeypatch, caplog):
    assert_command_error(capsys, monkeypatch, main, ['detect-format', '--root-path', 'nonexistent',
                                                     path('record_minimal.json')], error=StopIteration)

    assert len(caplog.records) == 0


def test_command_recursive(capsys, monkeypatch, caplog, tmpdir):
    content = b'{"records":[]}'
    tmpdir.join('test.json').write(content)
    tmpdir.join('.test.json').write(content)

    actual = run_command(capsys, monkeypatch, main, ['detect-format', '--recursive', str(tmpdir)])

    assert f'{os.sep}test.json: record package' in actual.out
    assert '.test.json' not in actual.out
    assert len(caplog.records) == 0


@pytest.mark.parametrize('basename,result', [
    ('false', 'boolean'),
    ('null', 'null'),
    ('number', 'number'),
    ('string', 'string'),
    ('true', 'boolean'),
    ('array', 'non-OCDS array'),
    ('object', 'non-OCDS object'),
])
def test_command_unknown_format(basename, result, capsys, monkeypatch, caplog):
    filename = f'detect-format_{basename}.json'

    expected = f'tests{os.sep}fixtures{os.sep}{filename}: unknown (top-level JSON value is a {result})'
    assert_command(capsys, monkeypatch, main, ['detect-format', path(filename)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == expected


def test_command_directory(capsys, monkeypatch, caplog, tmpdir):
    assert_command(capsys, monkeypatch, main, ['detect-format', str(tmpdir)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(capsys, monkeypatch, caplog):
    assert_command(capsys, monkeypatch, main, ['detect-format', 'nonexistent'], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'
