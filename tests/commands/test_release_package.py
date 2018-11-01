import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release_minimal1.json', 'rb') + read('release_minimal2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'release-package'])
        main()

    assert actual.getvalue() == read('release-package_minimal1-minimal2.json')


def test_command_extensions(monkeypatch):
    stdin = read('release_minimal1.json', 'rb') + read('release_minimal2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'release-package', 'http://example.com/a/extension.json',
                                          'http://example.com/b/extension.json'])
        main()

    assert actual.getvalue() == read('release-package_minimal1-minimal2-extensions.json')
