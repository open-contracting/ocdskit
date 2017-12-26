import io
import sys
from io import StringIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('realdata/release-package-1.json', 'rb') + read('realdata/release-package-2.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'compile'])
        main()

    assert actual.getvalue() == read('realdata/compiled-release-1.json') + read('realdata/compiled-release-2.json')

def test_command_pretty(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', '--pretty', 'compile'])
        main()

    assert actual.getvalue() == read('compile_pretty_minimal.json')
