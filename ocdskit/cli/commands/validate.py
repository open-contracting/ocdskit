import json
from urllib.parse import urlparse

import requests
import rfc3987
from jsonschema import FormatChecker
from jsonschema.compat import str_types
from jsonschema.validators import Draft4Validator as validator

from ocdskit.cli.commands.base import OCDSCommand


class Command(OCDSCommand):
    name = 'validate'
    help = 'reads JSON data from standard input, validates it against the schema, and prints errors'

    def add_arguments(self):
        self.add_argument('--schema', help='the URL or path of the schema to validate against',
                          default='https://standard.open-contracting.org/latest/en/release-package-schema.json')
        self.add_argument('--check-urls', help='check the HTTP status code if "format": "uri"', action='store_true')
        self.add_argument('--timeout', help='timeout (seconds) to GET a URL', type=int, default=10)
        self.add_argument('--verbose', help='print items without validation errors', action='store_true')

    def handle(self):
        components = urlparse(self.args.schema)
        if components.scheme == 'file':
            with open(self.args.schema[7:]) as f:
                schema = json.load(f)
        else:
            schema = requests.get(self.args.schema).json()

        format_checker = FormatChecker()
        if self.args.check_urls:
            def check_url(instance):
                # See https://github.com/Julian/jsonschema/blob/master/jsonschema/_format.py
                if not isinstance(instance, str_types):
                    return True
                rfc3987.parse(instance, rule='URI')  # raises ValueError
                try:
                    response = requests.get(instance, timeout=self.args.timeout)
                    result = response.status_code in (200,)
                    if not result:
                        print('HTTP {} on GET {}'.format(response.status_code, instance))
                    return result
                except requests.exceptions.Timeout:
                    print('Timedout on GET {}'.format(instance))
                    return False

            format_checker.checks('uri', raises=(ValueError))(check_url)

        for i, data in enumerate(self.items()):
            errors = False
            for error in validator(schema, format_checker=format_checker).iter_errors(data):
                print('item {}: {} ({})'.format(i, error.message, '/'.join(error.absolute_schema_path)))
                errors = True
            if not errors and self.args.verbose:
                print('item {}: no errors'.format(i))
