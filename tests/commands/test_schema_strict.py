import json
from io import StringIO
from unittest.mock import patch

from ocdskit.cli.__main__ import main
from tests import path, run_command

expected = '''{
  "required": [
    "array",
    "minItemsArray",
    "object",
    "minPropertiesObject",
    "string",
    "minLengthString",
    "enumString",
    "formatString",
    "patternString"
  ],
  "properties": {
    "optionalArray": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true
    },
    "array": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true
    },
    "minItemsArray": {
      "type": "array",
      "minItems": 2,
      "uniqueItems": true
    },
    "optionalObject": {
      "type": "object",
      "minProperties": 1
    },
    "object": {
      "type": "object",
      "minProperties": 1
    },
    "minPropertiesObject": {
      "type": "object",
      "minProperties": 2
    },
    "optionalString": {
      "type": "string",
      "minLength": 1
    },
    "string": {
      "type": "string",
      "minLength": 1
    },
    "minLengthString": {
      "type": "string",
      "minLength": 2
    },
    "enumString": {
      "type": "string",
      "enum": [
        "a"
      ]
    },
    "formatString": {
      "type": "string",
      "format": "uri"
    },
    "patternString": {
      "type": "string",
      "pattern": "."
    }
  }
}
'''


def test_command(monkeypatch, tmpdir):
    with open(path('schema-strict.json'), 'rb') as f:
        schema = f.read()

    p = tmpdir.join('schema.json')
    p.write(schema)

    run_command(monkeypatch, main, ['schema-strict', str(p)])

    assert p.read() == expected


def test_command_no_unique_items(monkeypatch, tmpdir):
    with open(path('schema-strict.json'), 'rb') as f:
        schema = f.read()

    p = tmpdir.join('schema.json')
    p.write(schema)

    run_command(monkeypatch, main, ['schema-strict', '--no-unique-items', str(p)])

    assert 'uniqueItems' not in json.loads(p.read())['properties']['array']


@patch('sys.stderr', new_callable=StringIO)
def test_command_check(stderr, monkeypatch):
    with open(path('schema-strict.json'), 'rb') as f:
        expected = f.read()

    run_command(monkeypatch, main, ['schema-strict', '--check', path('schema-strict.json')])

    with open(path('schema-strict.json'), 'rb') as f:
        assert f.read() == expected

    assert stderr.getvalue() == 'ERROR: tests/fixtures/schema-strict.json is missing validation properties\n'
