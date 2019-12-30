import sys
import os.path
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest


def path(filename):
    return os.path.join('tests', 'fixtures', filename)


def read(filename, mode='rt', encoding=None, **kwargs):
    with open(path(filename), mode, encoding=encoding, **kwargs) as f:
        return f.read()


def run_command(monkeypatch, main, args, stdin):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as stdout:
        monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
        main()

    return stdout.getvalue()


def assert_command_raises(monkeypatch, main, args, stdin):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as stdout:
            monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
            main()

    return stdout.getvalue(), excinfo


def assert_command(monkeypatch, main, args, stdin, expected):
    actual = run_command(monkeypatch, main, args, stdin)

    if not isinstance(expected, str):
        expected = ''.join(read(filename) for filename in expected)

    assert actual == expected
