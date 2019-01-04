import os.path
import sys
from io import StringIO
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest.mock import patch

from ocdskit.cli.__main__ import main

content = b'{"lorem":"ipsum"}'
invalid = b'{"lorem":"ipsum"'


def test_command(monkeypatch):
    with NamedTemporaryFile() as f:
        f.write(content)

        f.flush()

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', f.name])
            main()

        f.seek(0)

        assert actual.getvalue() == ''

        assert f.read() == b'{\n  "lorem": "ipsum"\n}\n'


def test_indent(monkeypatch):
    with NamedTemporaryFile() as f:
        f.write(content)

        f.flush()

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', '--indent', '4', f.name])
            main()

        f.seek(0)

        assert actual.getvalue() == ''

        assert f.read() == b'{\n    "lorem": "ipsum"\n}\n'


def test_command_recursive(monkeypatch):
    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'test.json'), 'wb') as f:
            f.write(content)

        with open(os.path.join(d, 'test.txt'), 'wb') as f:
            f.write(content)

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', '--recursive', d])
            main()

        assert actual.getvalue() == ''

        with open(os.path.join(d, 'test.json'), 'rb') as f:
            assert f.read() == b'{\n  "lorem": "ipsum"\n}\n'

        with open(os.path.join(d, 'test.txt'), 'rb') as f:
            assert f.read() == content


def test_command_directory(monkeypatch, caplog):
    with TemporaryDirectory() as d:
        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', d])
            main()

        assert actual.getvalue() == ''

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'WARNING'
        assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(monkeypatch, caplog):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', 'nonexistent'])
        main()

    assert actual.getvalue() == ''

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'


def test_command_invalid_json(monkeypatch, caplog):
    with NamedTemporaryFile() as f:
        f.write(invalid)

        f.flush()

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', f.name])
            main()

        f.seek(0)

        assert actual.getvalue() == ''

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'ERROR'
        assert ' is not valid JSON. (json.decoder.JSONDecodeError: ' in caplog.records[0].message
