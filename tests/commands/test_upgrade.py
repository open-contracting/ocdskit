import json

import pytest
from jsonpointer import set_pointer

from ocdskit.cli.__main__ import main
from tests import assert_streaming, assert_streaming_error, read, run_streaming


def test_command_record_package(monkeypatch):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'],
                     ['realdata/record-package_1.0.json'],
                     ['realdata/record-package_1.1.json'], ordered=False)


def test_command_record(monkeypatch):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1', '--root-path', 'records.item'],
                     ['realdata/record-package_package.json'],
                     ['realdata/record-package_package_1.1.json'], ordered=False)


def test_command_release_package_buyer_procuring_entity_suppliers(monkeypatch):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'],
                     ['realdata/release-package_1.0-1.json'],
                     ['realdata/release-package_1.1-1.json'], ordered=False)


def test_command_release_package_transactions(monkeypatch):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'],
                     ['realdata/release-package_1.0-2.json'],
                     ['realdata/release-package_1.1-2.json'], ordered=False)


def test_command_release_tenderers_amendment(monkeypatch, caplog):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'],
                     ['release_1.0.json'],
                     ['release_1.1.json'], ordered=False)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'WARNING'
    assert caplog.records[0].message == (
        'party differs in "supplier" role than in "tenderer" roles:\n'
        '{"name": "Acme Inc.", "identifier": {"id": 1}, "additionalIdentifiers": [{"id": "a"}], "id": "3c9756cf8983b14066a034079aa7aae4"}\n'  # noqa: E501
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
    run_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'], stdin)


def test_command_release_party_id_missing(monkeypatch):
    data = json.loads(read('release-package_minimal.json'))

    data['releases'][0]['parties'] = [{'name': 'Acme Inc.'}]
    del data['version']

    stdin = json.dumps(data).encode('utf-8')

    # Should not raise an error.
    run_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'], stdin)


def test_command_passthrough_package(monkeypatch, caplog):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'],
                     ['realdata/record-package_1.1.json'],
                     ['realdata/record-package_1.1.json'])

    assert len(caplog.records) == 0


def test_command_passthrough_release(monkeypatch, caplog):
    assert_streaming(monkeypatch, main, ['upgrade', '1.0:1.1'],
                     ['release_1.1.json'],
                     ['release_1.1.json'])

    assert len(caplog.records) == 0


@pytest.mark.parametrize('versions', ['1.0:1.0', '1.1:1.1'])
def test_command_identity(versions, monkeypatch):
    assert_streaming(monkeypatch, main, ['upgrade', versions], b'{}', '{}\n')


def test_command_downgrade(monkeypatch, caplog):
    stdin = b'{}'

    assert_streaming_error(monkeypatch, main, ['upgrade', '1.1:1.0'], stdin)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == 'CRITICAL'
    assert caplog.records[0].message == 'downgrade from 1.1 to 1.0 is not supported'
