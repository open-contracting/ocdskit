import pytest

from ocdskit.cli.__main__ import main
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
])
def test_command(filename, result, monkeypatch):
    expected = 'tests/fixtures/{}: {}\n'.format(filename, result)
    assert_command(monkeypatch, main, ['detect-format', path(filename)], expected)


@pytest.mark.parametrize('filename,root_path,result', [
    ('record-package_minimal.json', 'records', 'a JSON array of records'),
    ('record-package_minimal.json', 'records.item', 'record'),
])
def test_command_root_path(filename, root_path, result, monkeypatch):
    expected = 'tests/fixtures/{}: {}\n'.format(filename, result)
    assert_command(monkeypatch, main, ['detect-format', '--root-path', root_path, path(filename)], expected)


def test_command_root_path_nonexistent(monkeypatch, caplog):
    assert_command_error(monkeypatch, main, ['detect-format', '--root-path', 'nonexistent',
                                             path('record_minimal.json')], error=StopIteration)

    assert len(caplog.records) == 0


def test_command_recursive(monkeypatch, caplog, tmpdir):
    content = b'{"records":[]}'
    tmpdir.join('test.json').write(content)
    tmpdir.join('.test.json').write(content)

    actual = run_command(monkeypatch, main, ['detect-format', '--recursive', str(tmpdir)])

    assert '/test.json: record package' in actual
    assert '.test.json' not in actual
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
def test_command_unknown_format(basename, result, monkeypatch, caplog):
    filename = 'detect-format_{}.json'.format(basename)

    assert_command(monkeypatch, main, ['detect-format', path(filename)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == 'tests/fixtures/{}: unknown (top-level JSON value is a {})'.format(
        filename, result)


def test_command_directory(monkeypatch, caplog, tmpdir):
    assert_command(monkeypatch, main, ['detect-format', str(tmpdir)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(monkeypatch, caplog):
    assert_command(monkeypatch, main, ['detect-format', 'nonexistent'], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'
