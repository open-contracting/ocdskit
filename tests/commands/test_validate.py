import os
import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import read


def test_command(monkeypatch):
    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate'])
        main()

    assert actual.getvalue() == "item 0: 'version' is a required property (required)\n"


def test_command_invalid_json(monkeypatch, caplog):
    with caplog.atLevel('INFO'):
        stdin = b'{\n'

        with pytest.raises(SystemExit) as excinfo:
            with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO):
                monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate'])
                main()

        assert len(caplog.records()) == 1
        assert caplog.records()[0].levelname == 'CRITICAL'
        assert caplog.records()[0].message == "item 0: JSON error: Expecting property name enclosed in double " \
                                              "quotes: line 2 column 1 (char 2)"
        assert excinfo.value.code == 1


def test_command_valid_release_package_url(monkeypatch):
    url = 'http://standard.open-contracting.org/schema/1__0__3/release-package-schema.json'

    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert actual.getvalue() == ''


def test_command_valid_release_package_file(monkeypatch):
    url = 'file://{}'.format(os.path.realpath(os.path.join('tests', 'fixtures', 'release-package-schema.json')))

    stdin = read('realdata/release-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert actual.getvalue() == ''


def test_command_invalid_record_package(monkeypatch):
    url = 'http://standard.open-contracting.org/latest/en/record-package-schema.json'

    stdin = read('realdata/record-package-1.json', 'rb')

    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'validate', '--schema', url])
        main()

    assert "item 0: None is not of type 'string' (properties/records/items/properties/compiledRelease/properties/tender/properties/submissionMethod/items/type)" in actual.getvalue()  # noqa
