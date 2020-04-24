import json

from ocdskit.cli.__main__ import main
from tests import run_command

schema = b'''{
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
      "type": "array"
    },
    "array": {
      "type": "array"
    },
    "minItemsArray": {
      "type": "array",
      "minItems": 2
    },
    "optionalObject": {
      "type": "object"
    },
    "object": {
      "type": "object"
    },
    "minPropertiesObject": {
      "type": "object",
      "minProperties": 2
    },
    "optionalString": {
      "type": "string"
    },
    "string": {
      "type": "string"
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
    p = tmpdir.join('schema.json')
    p.write(schema)

    run_command(monkeypatch, main, ['schema-strict', str(p)])

    assert p.read() == expected


def test_command_no_unique_items(monkeypatch, tmpdir):
    p = tmpdir.join('schema.json')
    p.write(schema)

    run_command(monkeypatch, main, ['schema-strict', '--no-unique-items', str(p)])

    assert 'uniqueItems' not in json.loads(p.read())['properties']['array']
