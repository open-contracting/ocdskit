import json
import sys
from io import StringIO, TextIOWrapper, BytesIO
from unittest.mock import patch

import pytest
from jsonpointer import set_pointer

from ocdskit.cli.__main__ import main
from tests import read


def test_command_record_package(monkeypatch):
    stdin = read('realdata/record-package_1.0.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/record-package_1.1.json')


def test_command_release_package_buyer_procuring_entity_suppliers(monkeypatch):
    stdin = read('realdata/release-package_1.0-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/release-package_1.1-1.json')


def test_command_release_package_transactions(monkeypatch):
    stdin = read('realdata/release-package_1.0-2.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/release-package_1.1-2.json')


def test_command_release_tenderers_amendment(monkeypatch, caplog):
    stdin = read('release_1.0.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('release_1.1.json')

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == (
        'party differs in "supplier" role than in "tenderer" roles:\n'
        '{"name": "Acme Inc.", "identifier": {"id": 1}, "additionalIdentifiers": [{"id": "a"}], "id": "3c9756cf8983b14066a034079aa7aae4"}\n'  # noqa
        '{"id": "3c9756cf8983b14066a034079aa7aae4", "name": "Acme Inc.", "identifier": {"id": 1}}'
    )


@pytest.mark.parametrize('pointer', ('parties', 'buyer', 'tender', 'tender/procuringEntity', 'tender/tenderers',
                                     'awards', 'awards/0/suppliers', 'contracts', 'contracts/0/implementation',
                                     'contracts/0/implementation/transactions'))
def test_command_release_field_is_null(pointer, monkeypatch):
    data = json.loads(read('release_minimal.json'))

    parts = pointer.split('/')
    for i, part in enumerate(parts, 1):
        if i < len(parts):
            if parts[i] == '0':
                value = [{}]
            else:
                value = {}
        else:
            value = None
        set_pointer(data, '/' + '/'.join(parts[:i]), value)

    stdin = json.dumps(data).encode('utf-8')

    # Should not raise an error.
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()


def test_command_release_party_id_missing(monkeypatch):
    data = json.loads(read('release-package_minimal.json'))

    data['releases'][0]['parties'] = [{'name': 'Acme Inc.'}]
    del data['version']

    stdin = json.dumps(data).encode('utf-8')

    # Should not raise an error.
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))):
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()


def test_command_passthrough_package(monkeypatch, caplog):
    stdin = read('realdata/record-package_1.1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('realdata/record-package_1.1.json')

    assert len(caplog.records) == 0


def test_command_passthrough_release(monkeypatch, caplog):
    stdin = read('release_1.1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.0:1.1'])
        main()

    assert actual.getvalue() == read('release_1.1.json')

    assert len(caplog.records) == 0


def test_command_identity(monkeypatch):
    stdin = b'{}'

    for versions in ('1.0:1.0', '1.1:1.1'):
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', versions])
            main()

    assert actual.getvalue() == '{}\n'


def test_command_downgrade(monkeypatch, caplog):
    stdin = b'{}'

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'upgrade', '1.1:1.0'])
            main()

    assert actual.getvalue() == ''

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == 'downgrade from 1.1 to 1.0 is not supported'
    assert excinfo.value.code == 1
