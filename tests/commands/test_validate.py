import io
import sys
from io import StringIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('release-package-1.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate'])
        main()

    assert actual.getvalue() == "item 0: 'version' is a required property (required)\n"


def test_command_valid(monkeypatch):
    url = 'http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json'

    stdin = read('release-package-1.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert actual.getvalue() == ''


def test_command_invalid(monkeypatch):
    url = 'http://standard.open-contracting.org/latest/en/record-package-schema.json'

    stdin = read('record-package-1.json', 'rb')

    with patch('sys.stdin', io.TextIOWrapper(io.BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert "item 0: None is not of type 'string' (properties/records/items/properties/compiledRelease/properties/tender/properties/submissionMethod/items/type)" in actual.getvalue()  # noqa
