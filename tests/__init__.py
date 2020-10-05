import os.path
import sys
from difflib import ndiff
from io import BytesIO, StringIO, TextIOWrapper
from itertools import zip_longest
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
        assert actual == expected, ''.join(ndiff(actual.splitlines(1), expected.splitlines(1)))
    else:
        for a, b in zip_longest(actual.split('\n'), expected.split('\n'), fillvalue='{}'):
            if a != b != '':
                assert ocdskit.util.jsonlib.loads(a) == ocdskit.util.jsonlib.loads(b), '\n{}\n{}'.format(a, b)


@patch('sys.stdout', new_callable=StringIO)
def run_command(monkeypatch, main, args, stdout):
    monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
    main()

    return stdout.getvalue()


# Similar to `run_command`, but with `pytest.raises` block.
@patch('sys.stdout', new_callable=StringIO)
def assert_command_error(monkeypatch, main, args, stdout, expected='', error=SystemExit):
    with pytest.raises(error) as excinfo:
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


@patch('sys.stdout', new_callable=StringIO)
def run_streaming(monkeypatch, main, args, stdin, stdout):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
        monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
        main()

    return stdout.getvalue()


# Similar to `run_streaming`, but with `pytest.raises` block.
@patch('sys.stdout', new_callable=StringIO)
def assert_streaming_error(monkeypatch, main, args, stdin, stdout, expected='', error=SystemExit):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with pytest.raises(error) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
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
