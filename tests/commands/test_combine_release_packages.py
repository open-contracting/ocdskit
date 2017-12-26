import io
import sys
from io import StringIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release-package-minimal.json', 'rb') + \
            read('release-package-maximal.json', 'rb') + \
            read('release-package-extensions.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'combine-release-packages'])
        main()

    assert actual.getvalue() == read('combine-minimal-maximal-extensions.json')

def test_command_no_extensions(monkeypatch):
    stdin = read('release-package-minimal.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'combine-release-packages'])
        main()

    assert actual.getvalue() == read('combine-minimal.json')
