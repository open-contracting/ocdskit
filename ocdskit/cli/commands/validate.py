import json
from urllib.parse import urlparse

import requests
from jsonschema import FormatChecker
from jsonschema.validators import Draft4Validator as validator

from .base import BaseCommand
from ocdskit.exceptions import CommandError


class Command(BaseCommand):
    name = 'validate'
    help = 'reads JSON data from standard input, validates it against the schema, and prints errors'

    def add_arguments(self):
        self.add_argument('--schema', help='the schema to validate against',
                          default='http://standard.open-contracting.org/latest/en/release-package-schema.json')

    def handle(self):
        components = urlparse(self.args.schema)
        if components.scheme == 'file':
            with open(self.args.schema[7:]) as f:
                schema = json.loads(f.read())
        else:
            schema = requests.get(self.args.schema).json()

        for i, line in enumerate(self.buffer()):
            try:
                data = json.loads(line)
                for error in validator(schema, format_checker=FormatChecker()).iter_errors(data):
                    print('item {}: {} ({})'.format(i, error.message, '/'.join(error.absolute_schema_path)))
            except json.decoder.JSONDecodeError as e:
                raise CommandError('item {}: JSON error: {}'.format(i, e))
