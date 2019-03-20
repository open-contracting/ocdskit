import json
import sys
from io import BytesIO, StringIO, TextIOWrapper
from unittest.mock import patch

from ocdskit.cli.__main__ import main

stdin = b'''{
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


def test_command(monkeypatch):
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', '--pretty', 'schema-strict'])
        main()

    assert actual.getvalue() == '''{
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
      "type": "object"
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
      "type": "string"
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


def test_command_no_unique_items(monkeypatch):
    with patch('sys.stdin', TextIOWrapper(BytesIO(stdin))), patch('sys.stdout', new_callable=StringIO) as actual:
        monkeypatch.setattr(sys, 'argv', ['ocdskit', 'schema-strict', '--no-unique-items'])
        main()

    assert 'uniqueItems' not in json.loads(actual.getvalue())['properties']['array']
