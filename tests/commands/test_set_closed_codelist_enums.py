import os.path
import sys
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ocdskit.cli.__main__ import main

schema = '''{
  "properties": {
    "closedStringNull": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": false
    },
    "closedArrayNull": {
      "type": [
        "array",
        "null"
      ],
      "codelist": "b.csv",
      "openCodelist": false,
      "items": {
        "type": "string"
      }
    },
    "closedString": {
      "type": "string",
      "codelist": "c.csv",
      "openCodelist": false
    },
    "closedDisorder": {
      "type": "string",
      "codelist": "d.csv",
      "openCodelist": false,
      "enum": [
        "bar",
        "foo"
      ]
    },
    "open": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "e.csv",
      "openCodelist": true
    }
  }
}
'''

schema_with_enum = '''{
  "properties": {
    "closedStringNull": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": false,
      "enum": [
        "foo",
        "bar",
        null
      ]
    },
    "closedArrayNull": {
      "type": [
        "array",
        "null"
      ],
      "codelist": "b.csv",
      "openCodelist": false,
      "items": {
        "type": "string",
        "enum": [
          "foo",
          "bar"
        ]
      }
    },
    "closedString": {
      "type": "string",
      "codelist": "c.csv",
      "openCodelist": false,
      "enum": [
        "foo",
        "bar"
      ]
    },
    "closedDisorder": {
      "type": "string",
      "codelist": "d.csv",
      "openCodelist": false,
      "enum": [
        "bar",
        "foo"
      ]
    },
    "open": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "e.csv",
      "openCodelist": true
    }
  }
}
'''

codelist = 'Code\nfoo\nbar\n'


def test_command(monkeypatch):
    with TemporaryDirectory() as d:
        os.mkdir(os.path.join(d, 'codelists'))

        with open(os.path.join(d, 'release-schema.json'), 'w') as f:
            f.write(schema)

        for basename in ('a', 'b', 'c', 'd'):
            with open(os.path.join(d, 'codelists', '{}.csv'.format(basename)), 'w') as f:
                f.write(codelist)

        with patch('sys.stdout', new_callable=StringIO) as actual:
            monkeypatch.setattr(sys, 'argv', ['ocdskit', 'set-closed-codelist-enums', d])
            main()

        assert actual.getvalue() == ''

        with open(os.path.join(d, 'release-schema.json')) as f:
            assert f.read() == schema_with_enum


def test_conflicting_codelists(monkeypatch):
    pass


def test_unused_codelists(monkeypatch):
    pass
