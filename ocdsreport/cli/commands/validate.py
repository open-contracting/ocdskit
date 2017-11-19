import requests
from jsonschema import FormatChecker
from jsonschema.validators import Draft4Validator as validator

from .base import BaseCommand
from ocdskit.exceptions import CommandError


class Command(BaseCommand):
    name = 'validate'
    help = 'quickly validate OCDS data'

    def add_arguments(self):
        self.add_argument('--schema', help='the schema to validate against',
                          default='http://standard.open-contracting.org/schema/1__1__1/release-package-schema.json')
        self.add_argument('--limit', type=int, help='the number of items to validate')

    def handle(self, args, data):
        schema = requests.get(args.schema).json()

        if isinstance(data, dict):
            data = [data]

        for i, item in enumerate(data[0:args.limit]):
            if not validator(schema, format_checker=FormatChecker()).is_valid(item):
                raise CommandError('item {} is invalid'.format(i))
