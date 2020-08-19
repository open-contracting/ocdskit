import json

from ocdskit.cli.commands.base import BaseCommand
from ocdskit.util import json_dump


class Command(BaseCommand):
    name = 'schema-strict'
    help = 'adds "minItems" and "uniqueItems" if an array, "minProperties" if an object and "minLength" if a ' \
           'string and "enum", "format" and "pattern" are not set'

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--no-unique-items', action='store_true',
                          help="""don't add "uniqueItems" properties to array fields""")

    def handle(self):
        def recurse(data):
            if isinstance(data, list):
                for item in data:
                    recurse(item)
            elif isinstance(data, dict):
                if 'type' in data:
                    if ('string' in data['type'] and 'enum' not in data and 'format' not in data
                            and 'pattern' not in data):
                        data.setdefault('minLength', 1)
                    if 'array' in data['type']:
                        data.setdefault('minItems', 1)
                        if not self.args.no_unique_items:
                            data.setdefault('uniqueItems', True)

                    if 'object' in data['type']:
                        data.setdefault('minProperties', 1)

                for value in data.values():
                    recurse(value)

        with open(self.args.file) as f:
            schema = json.load(f)

        recurse(schema)

        with open(self.args.file, 'w') as f:
            json_dump(schema, f, indent=2)
            f.write('\n')
