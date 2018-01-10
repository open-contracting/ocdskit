import sys
from io import StringIO
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    with NamedTemporaryFile() as f:
        f.write(b'{"lorem":"ipsum"}')

        f.flush()

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'indent', f.name])
            main()

        f.seek(0)

        assert actual.getvalue() == ''
        assert f.read() == b'{\n  "lorem": "ipsum"\n}\n'
