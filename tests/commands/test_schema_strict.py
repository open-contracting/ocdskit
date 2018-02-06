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
    "array": {
      "type": "array"
    },
    "minItemsArray": {
      "type": "array",
      "minItems": 2
    },
    "object": {
      "type": "object"
    },
    "minPropertiesObject": {
      "type": "object",
      "minProperties": 2
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
    "array": {
      "type": "array",
      "minItems": 1
    },
    "minItemsArray": {
      "type": "array",
      "minItems": 2
    },
    "object": {
      "type": "object",
      "minProperties": 1
    },
    "minPropertiesObject": {
      "type": "object",
      "minProperties": 2
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
