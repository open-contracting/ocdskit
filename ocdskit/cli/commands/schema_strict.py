from ocdskit.cli.commands.base import BaseCommand


class Command(BaseCommand):
    name = 'schema-strict'
    help = 'adds "minItems" and "uniqueItems" if an array, "minProperties" if an object and "minLength" if a ' \
           'string and "enum", "format" and "pattern" are not set'

    def add_arguments(self):
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
                        if 'minLength' not in data:
                            data['minLength'] = 1
                    if 'array' in data['type']:
                        if 'minItems' not in data:
                            data['minItems'] = 1
                        if not self.args.no_unique_items:
                            if 'uniqueItems' not in data:
                                data['uniqueItems'] = True

                    if 'object' in data['type']:
                        if 'minProperties' not in data:
                            data['minProperties'] = 1

                for value in data.values():
                    recurse(value)

        for schema in self.items():
            recurse(schema)
            self.print(schema)
