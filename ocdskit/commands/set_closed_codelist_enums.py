import csv
import itertools
import json
import logging
import os.path
from copy import deepcopy

from ocdskit.commands.base import BaseCommand
from ocdskit.util import _cast_as_list, json_dump

logger = logging.getLogger('ocdskit')

meta_schema_exceptions = {
    'meta-schema.json',
    'meta-schema-patch.json',
}


class Command(BaseCommand):
    name = 'set-closed-codelist-enums'
    help = 'sets the enum in a JSON Schema to match the codes in the CSV files of closed codelists'

    def __init__(self, subparsers):
        super().__init__(subparsers)

        self.codelists = {}
        self.codelists_seen = set()

    def add_arguments(self):
        self.add_argument('standard', help='path to directory containing standard JSON Schema files')
        self.add_argument('extension', help='paths to directories containing extension JSON Schema files', nargs='*')

    def handle(self):
        if self.args.extension:
            self.collect_codelists(self.args.standard)
            self.codelists_seen = set(self.codelists)
            directories = self.args.extension
        else:
            directories = [self.args.standard]

        for directory in directories:
            self.collect_codelists(directory)
            self.update_json_schema(directory)

        codelists_not_seen = []
        for codelist in self.codelists:
            if codelist not in self.codelists_seen:
                codelists_not_seen.append(codelist)

        if codelists_not_seen:
            logger.error('unused codelists: %s', ' '.join(codelists_not_seen))

    def collect_codelists(self, directory):
        for root, _, files in os.walk(directory):
            for name in files:
                if name.endswith('.csv'):
                    with open(os.path.join(root, name)) as f:
                        reader = csv.DictReader(f)
                        row = next(reader)
                        if 'Code' in row:
                            codes = [row['Code'] for row in itertools.chain([row], reader)]
                        else:
                            codes = []

                    if codes:
                        if name.startswith('+'):
                            # KeyError if codelist doesn't exist.
                            self.codelists[name[1:]] += codes
                        elif name.startswith('-'):
                            # KeyError if codelist doesn't exist.
                            self.codelists[name[1:]] = [code for code in self.codelists[name[1:]] if code not in codes]
                        elif name in self.codelists:
                            if self.codelists[name] != codes:
                                logger.error('conflicting codelists: %s', name)
                        else:
                            self.codelists[name] = codes

    # This method is similar to `validate_codelist_enum` in `test_json.py`.
    def update_codelist_enum(self, data):
        if isinstance(data, list):
            return [self.update_codelist_enum(item) for item in data]

        if isinstance(data, dict) and 'codelist' not in data:
            return {key: self.update_codelist_enum(value) for key, value in data.items()}

        if isinstance(data, dict) and 'codelist' in data:
            self.codelists_seen.add(data['codelist'])

            if not data['openCodelist']:
                codes = self.codelists[data['codelist']]

                types = _cast_as_list(data['type'])

                if 'string' in types:
                    if 'null' in types:
                        codes.append(None)
                    if 'enum' not in data or set(data['enum']) != set(codes):
                        data['enum'] = codes
                elif 'array' in types:
                    if 'enum' not in data['items'] or set(data['items']['enum']) != set(codes):
                        data['items']['enum'] = codes

        return data

    def update_json_schema(self, directory):
        for root, _, files in os.walk(directory):
            for name in files:
                if name.endswith('.json') and name not in meta_schema_exceptions:
                    path = os.path.join(root, name)

                    with open(path) as f:
                        data = json.load(f)

                    # If the JSON file is a JSON Schema file.
                    if any(field in data for field in ('$schema', 'definitions', 'properties')):
                        expected = deepcopy(data)
                        self.update_codelist_enum(data)

                        if expected != data:
                            with open(path, 'w') as f:
                                json_dump(data, f, indent=2)
                                f.write('\n')
