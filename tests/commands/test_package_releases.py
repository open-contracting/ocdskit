from ocdskit.cli.__main__ import main
from tests import assert_streaming


def test_command(monkeypatch):
    assert_streaming(monkeypatch, main, ['package-releases', '--uri', 'http://example.com', '--published-date',
                                         '9999-01-01T00:00:00Z', '--version', '1.2', '--publisher-name', ''],
                     ['release_minimal-1.json', 'release_minimal-2.json'],
                     ['release-package_minimal-1-2.json'])


def test_command_size(monkeypatch):
    assert_streaming(monkeypatch, main, ['package-releases', '--size', '2'],
                     ['release_minimal-1.json', 'release_minimal-2.json', 'release_minimal.json'],
                     ['release-package_minimal-1-2-no-metadata.json', 'release-package_minimal-no-metadata.json'])


def test_command_extensions(monkeypatch):
    assert_streaming(monkeypatch, main, ['package-releases', '--uri', 'http://example.com', '--published-date',
                                         '9999-01-01T00:00:00Z', '--version', '1.2', '--publisher-name', '',
                                         'http://example.com/a/extension.json', 'http://example.com/b/extension.json'],
                     ['release_minimal-1.json', 'release_minimal-2.json'],
                     ['release-package_minimal-1-2-extensions.json'])


def test_command_root_path_array(monkeypatch):
    assert_streaming(monkeypatch, main, ['package-releases', '--root-path', 'records.item.releases'],
                     ['realdata/record-package-1.json', 'realdata/record-package-2.json'],
                     ['realdata/release-package_record-package.json'])


def test_command_root_path_item(monkeypatch):
    assert_streaming(monkeypatch, main, ['package-releases', '--root-path', 'records.item.releases.item'],
                     ['realdata/record-package-1.json', 'realdata/record-package-2.json'],
                     ['realdata/release-package_record-package.json'])
