import sys
from io import StringIO
from unittest.mock import patch

import pytest

from ocdskit.cli.__main__ import main
from tests import path

test_command_argvalues = [
    ('record-package_minimal.json', 'record package'),
    ('release-package_minimal.json', 'release package'),
    ('record_minimal.json', 'record'),
    ('release_minimal.json', 'release'),
    ('realdata/compiled-release-1.json', 'compiled release'),
    ('realdata/versioned-release-1.json', 'versioned release'),
    ('release-packages.json', 'a JSON array of release packages'),
    ('release-packages.jsonl', 'concatenated JSON, starting with a JSON array of release packages'),
]


@pytest.mark.parametrize('filename,result', test_command_argvalues)
def test_command(filename, result, monkeypatch):
    with patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'detect-format', path(filename)])
        main()

    assert actual.getvalue() == 'tests/fixtures/{}: {}\n'.format(filename, result)
