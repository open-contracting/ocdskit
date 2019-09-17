import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release_minimal-1.json', 'rb') + read('release_minimal-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'package-releases', '--uri', 'http://example.com',
                                          '--published-date', '9999-01-01T00:00:00Z', '--publisher-name', ''])
        main()

    assert actual.getvalue() == read('release-package_minimal-1-2.json')


def test_command_extensions(monkeypatch):
    stdin = read('release_minimal-1.json', 'rb') + read('release_minimal-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'package-releases', '--uri', 'http://example.com',
                                          '--published-date', '9999-01-01T00:00:00Z', '--publisher-name', '',
                                          'http://example.com/a/extension.json',
                                          'http://example.com/b/extension.json'])
        main()

    assert actual.getvalue() == read('release-package_minimal-1-2-extensions.json')


def test_command_root_path_array(monkeypatch):
    stdin = read('realdata/record-package-1.json', 'rb') + read('realdata/record-package-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'package-releases', '--root-path', 'records.item.releases'])
        main()

    assert actual.getvalue() == read('realdata/release-package_record-package.json')


def test_command_root_path_item(monkeypatch):
    stdin = read('realdata/record-package-1.json', 'rb') + read('realdata/record-package-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'package-releases', '--root-path', 'records.item.releases.item'])
        main()

    assert actual.getvalue() == read('realdata/release-package_record-package.json')
