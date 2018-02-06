import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

from ocdskit.cli.__main__ import main

stdin = b'''{
  "properties": {
    "open": {
      "type": [
        "string",
        "null"
      ],
      "codelist": "a.csv",
      "openCodelist": true
    },
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
    }
  }
}
'''


def test_command(monkeypatch):
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'schema-report'])
        main()

    assert actual.getvalue() == '''openCodelist: False
a.csv
b.csv
c.csv
d.csv

'''
