import json
from collections import OrderedDict

from .base import BaseCommand


class Command(BaseCommand):
    name = 'schema-strict'
    help = 'for any required field, adds "minItems" if an array, "minProperties" if an object and "minLength" if a ' \
           'string and "enum", "format" and "pattern" are not set'

    def handle(self):
        def recurse(data):
            if isinstance(data, list):
                for item in data:
                    recurse(item)
            elif isinstance(data, dict):
                if 'required' in data:
                    for name in data['required']:
                        definition = data['properties'][name]
                        if ('string' in definition['type'] and 'enum' not in definition and 'format' not in definition
                                and 'pattern' not in definition):
                            if 'minLength' not in definition:
                                definition['minLength'] = 1
                        if 'array' in definition['type']:
                            if 'minItems' not in definition:
                                definition['minItems'] = 1
                        if 'object' in definition['type']:
                            if 'minProperties' not in definition:
                                definition['minProperties'] = 1
                for value in data.values():
                    recurse(value)

        schema = json.load(self.buffer(), object_pairs_hook=OrderedDict)
        recurse(schema)
        self.print(schema)
