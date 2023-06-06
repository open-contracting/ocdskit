import os.path
import sys
from difflib import ndiff
from io import BytesIO, TextIOWrapper
from itertools import zip_longest
from unittest.mock import patch

import pytest

import ocdskit.util


def path(filename):
    return os.path.join('tests', 'fixtures', filename)


def read(filename, mode='rt', **kwargs):
    if 'b' not in mode:
        kwargs['encoding'] = 'utf-8'
    with open(path(filename), mode, **kwargs) as f:
        return f.read()


def assert_equal(actual, expected, ordered=True):
    if ordered:
        assert actual == expected, ''.join(ndiff(expected.splitlines(1), actual.splitlines(1)))
    else:
        for a, b in zip_longest(actual.split('\n'), expected.split('\n'), fillvalue='{}'):
            if a != b != '':
                assert ocdskit.util.jsonlib.loads(a) == ocdskit.util.jsonlib.loads(b), f'\n{a}\n{b}'


def run_command(capsys, monkeypatch, main, args):
    monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
    main()

    return capsys.readouterr()


# Similar to `run_command`, but with `pytest.raises` block.
def assert_command_error(capsys, monkeypatch, main, args, expected='', error=SystemExit):
    with pytest.raises(error) as excinfo:
        monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
        main()

    actual = capsys.readouterr()

    assert actual.out == expected, f'\n{actual.out}\n{expected}'
    if error is SystemExit:
        assert excinfo.value.code == 1

    return excinfo


def assert_command(capsys, monkeypatch, main, args, expected, ordered=True):
    actual = run_command(capsys, monkeypatch, main, args)

    if os.path.isfile(path(expected)):
        expected = read(expected, newline='')

    assert_equal(actual.out, expected, ordered=ordered)


def run_streaming(capsys, monkeypatch, main, args, stdin):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
        monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
        main()

    return capsys.readouterr()


# Similar to `run_streaming`, but with `pytest.raises` block.
def assert_streaming_error(capsys, monkeypatch, main, args, stdin, expected='', error=SystemExit):
    if not isinstance(stdin, bytes):
        stdin = b''.join(read(filename, 'rb') for filename in stdin)

    with pytest.raises(error) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
            monkeypatch.setattr(sys, 'argv', ['ocdskit'] + args)
            main()

    actual = capsys.readouterr()

    assert actual.out == expected, f'\n{actual.out}\n{expected}'
    if error is SystemExit:
        assert excinfo.value.code == 1

    return excinfo


def assert_streaming(capsys, monkeypatch, main, args, stdin, expected, ordered=True):
    actual = run_streaming(capsys, monkeypatch, main, args, stdin)

    if not isinstance(expected, str):
        expected = ''.join(read(filename) for filename in expected)

    assert_equal(actual.out, expected, ordered=ordered)
