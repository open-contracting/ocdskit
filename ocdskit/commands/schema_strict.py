import json
import sys
from copy import deepcopy

from ocdskit.commands.base import BaseCommand
from ocdskit.schema import add_validation_properties
from ocdskit.util import json_dump


class Command(BaseCommand):
    name = 'schema-strict'
    help = 'adds "minItems" and "uniqueItems" if an array, "minProperties" if an object and "minLength" if a ' \
           'string and "enum", "format" and "pattern" are not set'

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--no-unique-items', action='store_true',
                          help="""don't add "uniqueItems" properties to array fields""")
        self.add_argument('--check', action='store_true',
                          help='check the file for missing properties without modifying the file')

    def handle(self):
        with open(self.args.file) as f:
            schema = json.load(f)

        original = deepcopy(schema)
        add_validation_properties(schema, unique_items=not self.args.no_unique_items)

        if self.args.check:
            if schema != original:
                print(f'ERROR: {self.args.file} is missing validation properties', file=sys.stderr)
        else:
            with open(self.args.file, 'w') as f:
                json_dump(schema, f, indent=2)
                f.write('\n')
