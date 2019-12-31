import os.path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from ocdskit.cli.__main__ import main
from tests import assert_command

content = b'{"lorem":"ipsum"}'
invalid = b'{"lorem":"ipsum"'


def test_command(monkeypatch):
    with NamedTemporaryFile() as f:
        f.write(content)
        f.flush()

        assert_command(monkeypatch, main, ['indent', f.name], '')
        f.seek(0)

        assert f.read() == b'{\n  "lorem": "ipsum"\n}\n'


def test_indent(monkeypatch):
    with NamedTemporaryFile() as f:
        f.write(content)
        f.flush()

        assert_command(monkeypatch, main, ['indent', '--indent', '4', f.name], '')
        f.seek(0)

        assert f.read() == b'{\n    "lorem": "ipsum"\n}\n'


def test_command_recursive(monkeypatch):
    with TemporaryDirectory() as d:
        with open(os.path.join(d, 'test.json'), 'wb') as f:
            f.write(content)
        with open(os.path.join(d, 'test.txt'), 'wb') as f:
            f.write(content)

        assert_command(monkeypatch, main, ['indent', '--recursive', d], '')

        with open(os.path.join(d, 'test.json'), 'rb') as f:
            assert f.read() == b'{\n  "lorem": "ipsum"\n}\n'
        with open(os.path.join(d, 'test.txt'), 'rb') as f:
            assert f.read() == content


def test_command_directory(monkeypatch, caplog):
    with TemporaryDirectory() as d:
        assert_command(monkeypatch, main, ['indent', d], '')

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'WARNING'
        assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(monkeypatch, caplog):
    assert_command(monkeypatch, main, ['indent', 'nonexistent'], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'


def test_command_invalid_json(monkeypatch, caplog):
    with NamedTemporaryFile() as f:
        f.write(invalid)
        f.flush()

        assert_command(monkeypatch, main, ['indent', f.name], '')

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == 'ERROR'
        assert ' is not valid JSON. (json.decoder.JSONDecodeError: ' in caplog.records[0].message
