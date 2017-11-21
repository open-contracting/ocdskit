import io
import sys
from io import StringIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release-package-1.json', 'rb') + read('release-package-2.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'compile'])
        main()

    assert actual.getvalue() == read('compiled-release-1.json') + read('compiled-release-2.json')
