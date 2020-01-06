import os.path
import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

import ocdskit.util


def path(filename):
    return os.path.join('tests', 'fixtures', filename)


def read(filename, mode='rt', encoding=None, **kwargs):
    with open(path(filename), mode, encoding=encoding, **kwargs) as f:
        return f.read()


def assert_equal(actual, expected, ordered=True):
    if ordered:
        assert actual == expected, '\n{}\n{}'.format(actual, expected)
    else:
        assert ocdskit.util.jsonlib.loads(actual) == ocdskit.util.jsonlib.loads(expected)


def run_command(monkeypatch, main, args):
    with patch('sys.stdout', new_callable=StringIO) as stdout:
        monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
        main()

    return stdout.getvalue()


# Similar to `run_command`, but with `pytest.raises` block.
def assert_command_error(monkeypatch, main, args, expected='', error=SystemExit):
    with pytest.raises(error) as excinfo:
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
            main()

    actual = stdout.getvalue()

    assert actual == expected, '\n{}\n{}'.format(actual, expected)
    if error is SystemExit:
        assert excinfo.value.code == 1

    return excinfo


def assert_command(monkeypatch, main, args, expected, ordered=True):
    actual = run_command(monkeypatch, main, args)

    if os.path.isfile(path(expected)):
        expected = read(expected, newline='')

    assert_equal(actual, expected, ordered=ordered)


def run_streaming(monkeypatch, main, args, stdin):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as stdout:
        monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
        main()

    return stdout.getvalue()


# Similar to `run_streaming`, but with `pytest.raises` block.
def assert_streaming_error(monkeypatch, main, args, stdin, expected='', error=SystemExit):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with pytest.raises(error) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as stdout:
            monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
            main()

    actual = stdout.getvalue()

    assert actual == expected, '\n{}\n{}'.format(actual, expected)
    if error is SystemExit:
        assert excinfo.value.code == 1

    return excinfo


def assert_streaming(monkeypatch, main, args, stdin, expected, ordered=True):
    actual = run_streaming(monkeypatch, main, args, stdin)

    if not isinstance(expected, str):
        expected = ''.join(read(filename) for filename in expected)

    assert_equal(actual, expected, ordered=ordered)
