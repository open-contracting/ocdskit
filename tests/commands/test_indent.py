from ocdskit.__main__ import main
from tests import assert_command

content = b'{"lorem":"ipsum"}'
invalid = b'{"lorem":"ipsum"'


def test_command(capsys, monkeypatch, tmpdir):
    p = tmpdir.join('test.json')
    p.write(content)

    assert_command(capsys, monkeypatch, main, ['indent', str(p)], '')

    assert p.read() == '{\n  "lorem": "ipsum"\n}\n'


def test_indent(capsys, monkeypatch, tmpdir):
    p = tmpdir.join('test.json')
    p.write(content)

    assert_command(capsys, monkeypatch, main, ['indent', '--indent', '4', str(p)], '')

    assert p.read() == '{\n    "lorem": "ipsum"\n}\n'


def test_ascii(capsys, monkeypatch, tmpdir):
    p = tmpdir.join('test.json')
    p.write(b'{"lorem":"ips\\u00fam"}')

    assert_command(capsys, monkeypatch, main, ['--ascii', 'indent', str(p)], '')

    assert p.read() == '{\n  "lorem": "ips\\u00fam"\n}\n'


def test_command_recursive(capsys, monkeypatch, tmpdir):
    tmpdir.join('test.json').write(content)
    tmpdir.join('test.txt').write(content)

    assert_command(capsys, monkeypatch, main, ['indent', '--recursive', str(tmpdir)], '')

    assert tmpdir.join('test.json').read() == '{\n  "lorem": "ipsum"\n}\n'
    assert tmpdir.join('test.txt').read() == content.decode()


def test_command_directory(capsys, monkeypatch, caplog, tmpdir):
    assert_command(capsys, monkeypatch, main, ['indent', str(tmpdir)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message.endswith(' is a directory. Set --recursive to recurse into directories.')


def test_command_nonexistent(capsys, monkeypatch, caplog):
    assert_command(capsys, monkeypatch, main, ['indent', 'nonexistent'], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert caplog.records[0].message == 'nonexistent: No such file or directory'


def test_command_invalid_json(capsys, monkeypatch, caplog, tmpdir):
    p = tmpdir.join('test.json')
    p.write(invalid)

    assert_command(capsys, monkeypatch, main, ['indent', str(p)], '')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'ERROR'
    assert ' is not valid JSON. (json.decoder.JSONDecodeError: ' in caplog.records[0].message
