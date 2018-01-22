import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('check_url_release-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'check_documents_urls', '--timeout', '1'])
        main()

    assert actual.getvalue() == "https://www.google.com status: 200\nnotfound status: malformed " \
                                "url\nhttps://www.google.com status: 200\nhttps://www.google.com status: " \
                                "200\nnotfound status: malformed url\nhttps://www.google.com status: " \
                                "200\nhttps://www.google.com status: 200\nhttps://www.google.com status: " \
                                "200\nhttps://www.google.com status: 200\nhttps://www.google.com status: 200\n"


def test_empty_documents(monkeypatch):
    stdin = read('release-package_minimal.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'check_documents_urls', '--timeout', '1'])
        main()

    assert actual.getvalue() == ""
