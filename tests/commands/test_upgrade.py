import json
import sys
from io import StringIO, TextIOWrapper, BytesIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import read


def test_command_record(monkeypatch):

    stdin = read('realdata/record_package_1_0.json', 'rb')
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()
    print(actual.getvalue())

    data = json.loads(actual.getvalue())
    assert data['version'] == '1.1'
    assert len(data['records'][0]['compiledRelease']['parties']) == 2
    assert 'contactPoint' not in data['records'][0]['compiledRelease']['buyer']


def test_command_release(monkeypatch):

    stdin = read('realdata/release_package_1_0.json', 'rb')
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()
    data = json.loads(actual.getvalue())
    assert data['version'] == '1.1'
    assert len(data['releases'][0]['parties']) == 2
    assert 'contactPoint' not in data['releases'][0]['buyer']


def test_command_release_contracts(monkeypatch):

    stdin = read('realdata/release_package_1_0_contracts.json', 'rb')
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()
    data = json.loads(actual.getvalue())
    assert data['version'] == '1.1'
    payee = data['releases'][0]['contracts'][0]['implementation']['transactions'][0]['payee']
    assert payee['id'] == '745a4d642e0e904e935a8fbd93b5366e'
