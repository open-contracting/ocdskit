import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb') + \
            read('release-package_maximal.json', 'rb') + \
            read('release-package_extensions.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'combine-release-packages'])
        main()

    assert actual.getvalue() == read('combine-release-packages_minimal-maximal-extensions.json')


def test_command_no_extensions(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'combine-release-packages'])
        main()

    assert actual.getvalue() == read('combine-release-packages_minimal.json')
