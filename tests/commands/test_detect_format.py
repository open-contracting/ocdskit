import os.path
import sys
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import path

test_command_argvalues = [
    ('record-package_minimal.json', 'record package'),
    ('release-package_minimal.json', 'release package'),
    ('record_minimal.json', 'record'),
    ('release_minimal.json', 'release'),
    ('realdata/compiled-release-1.json', 'compiled release'),
    ('realdata/versioned-release-1.json', 'versioned release'),
    ('release-packages.json', 'a JSON array of release packages'),
    ('release-packages.jsonl', 'concatenated JSON, starting with a JSON array of release packages'),
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

content = b'{"lorem":"ipsum"}'


@pytest.mark.parametrize('basename,result', test_command_unknown_format_argvalues)
def test_command_unknown_format(basename, result, monkeypatch, caplog):
    filename = 'detect-format_{}.json'.format(basename)

    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'detect-format', path(filename)])
        main()

    assert actual.getvalue() == ''

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == 'tests/fixtures/{}: unknown (top-level JSON value is a {})'.format(filename, result)  # noqa


@pytest.mark.parametrize('filename,result', test_command_argvalues)
def test_command(filename, result, monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'detect-format', path(filename)])
        main()

    assert actual.getvalue() == 'tests/fixtures/{}: {}\n'.format(filename, result)


def test_command_recursive(monkeypatch):
    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'test.json'), 'wb') as f:
            f.write(content)

        with open(os.path.join(d, '.test.json'), 'wb') as f:
            f.write(content)

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'detect-format', '--recursive', d])
            main()

        assert actual.getvalue() == ''


def test_command_directory(monkeypatch, caplog):
    with TemporaryDirectory() as d:
        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'detect-format', d])
            main()

        assert actual.getvalue() == ''

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'WARNING'
        assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(monkeypatch, caplog):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'detect-format', 'nonexistent'])
        main()

    assert actual.getvalue() == ''

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'
