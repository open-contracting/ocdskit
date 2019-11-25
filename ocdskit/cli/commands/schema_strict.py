from ocdskit.cli.commands.base import BaseCommand


class Command(BaseCommand):
    name = 'schema-strict'
    help = 'for any required field, adds "minItems" if an array, "minProperties" if an object and "minLength" if a ' \
           'string and "enum", "format" and "pattern" are not set, and for any array field, adds "uniqueItems"'

    def add_arguments(self):
        self.add_argument('--no-unique-items', action='store_true',
                          help="""don't add "uniqueItems" properties to array fields""")

    def handle(self):
        def recurse(data):
            if isinstance(data, list):
                for item in data:
                    recurse(item)
            elif isinstance(data, dict):
                if not self.args.no_unique_items and 'type' in data and 'array' in data['type']:
                    if 'uniqueItems' not in data:
                        data['uniqueItems'] = True

                if 'required' in data:
                    for name in data['required']:
                        definition = data['properties'][name]
                        if 'type' in definition:
                            definition_type = definition['type']
                        else:
                            definition_type = []

                        if ('string' in definition_type and 'enum' not in definition and 'format' not in definition
                                and 'pattern' not in definition):
                            if 'minLength' not in definition:
                                definition['minLength'] = 1
                        if 'array' in definition_type:
                            if 'minItems' not in definition:
                                definition['minItems'] = 1
                        if 'object' in definition_type:
                            if 'minProperties' not in definition:
                                definition['minProperties'] = 1

                for value in data.values():
                    recurse(value)

        for schema in self.items():
            recurse(schema)
            self.print(schema)
