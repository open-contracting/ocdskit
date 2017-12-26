import io
import sys
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=io.StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'tabulate', 'sqlite://'])
        main()

    assert actual.getvalue() == ''
