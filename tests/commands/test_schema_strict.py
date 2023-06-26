import json
import os

from ocdskit.__main__ import main
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
      "uniqueItems": true,
      "minItems": 1
    },
    "array": {
      "type": "array",
      "uniqueItems": true,
      "minItems": 1
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
    },
    "coordinates": {
      "type": "array",
      "items": {
        "type": [
          "number",
          "array"
        ],
        "minItems": 1
      },
      "minItems": 1
    }
  }
}
'''


def test_command(capsys, monkeypatch, tmpdir):
    with open(path('schema-strict.json'), 'rb') as f:
        schema = f.read()

    p = tmpdir.join('schema.json')
    p.write(schema)

    run_command(capsys, monkeypatch, main, ['schema-strict', str(p)])

    assert p.read() == expected


def test_command_no_unique_items(capsys, monkeypatch, tmpdir):
    with open(path('schema-strict.json'), 'rb') as f:
        schema = f.read()

    p = tmpdir.join('schema.json')
    p.write(schema)

    run_command(capsys, monkeypatch, main, ['schema-strict', '--no-unique-items', str(p)])

    assert 'uniqueItems' not in json.loads(p.read())['properties']['array']


def test_command_check(capsys, monkeypatch):
    with open(path('schema-strict.json'), 'rb') as f:
        expected = f.read()

    captured = run_command(capsys, monkeypatch, main, ['schema-strict', '--check', path('schema-strict.json')])

    with open(path('schema-strict.json'), 'rb') as f:
        assert f.read() == expected

    assert captured.err == f'ERROR: tests{os.sep}fixtures{os.sep}schema-strict.json is missing validation properties\n'
