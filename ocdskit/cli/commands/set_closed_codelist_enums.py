import csv
import itertools
import json
import logging
import os.path
from copy import deepcopy

from ocdskit.cli.commands.base import BaseCommand
from ocdskit.util import json_dump

logger = logging.getLogger('ocdskit')


class Command(BaseCommand):
    name = 'set-closed-codelist-enums'
    help = 'sets the enum in a JSON Schema to match the codes in the CSV files of closed codelists'

    def add_arguments(self):
        self.add_argument('standard', help='path to directory containing standard JSON Schema files')
        self.add_argument('extension', help='paths to directories containing extension JSON Schema files', nargs='*')

    def handle(self):
        def collect_codelists(directory):
            for root, dirs, files in os.walk(directory):
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
                                codelists[name[1:]] += codes
                            elif name.startswith('-'):
                                # KeyError if codelist doesn't exist.
                                codelists[name[1:]] = [code for code in codelists[name[1:]] if code not in codes]
                            elif name in codelists:
                                if codelists[name] != codes:
                                    logger.error('conflicting codelists: {}'.format(name))
                            else:
                                codelists[name] = codes

        # This method is similar to `validate_codelist_enum` in `test_json.py`.
        def update_codelist_enum(data):
            if isinstance(data, list):
                return [update_codelist_enum(item) for item in data]

            if isinstance(data, dict) and 'codelist' not in data:
                return {key: update_codelist_enum(value) for key, value in data.items()}

            if isinstance(data, dict) and 'codelist' in data:
                codelists_seen.add(data['codelist'])

                if not data['openCodelist']:
                    codes = codelists[data['codelist']]

                    if isinstance(data['type'], str):
                        types = [data['type']]
                    else:
                        types = data['type']

                    if 'string' in types:
                        if 'null' in types:
                            codes.append(None)
                        if 'enum' not in data or set(data['enum']) != set(codes):
                            data['enum'] = codes
                    elif 'array' in types:
                        if 'enum' not in data['items'] or set(data['items']['enum']) != set(codes):
                            data['items']['enum'] = codes

            return data

        def update_json_schema(directory):
            for root, dirs, files in os.walk(directory):
                for name in files:
                    if name.endswith('.json') and name not in meta_schema_exceptions:
                        path = os.path.join(root, name)

                        with open(path) as f:
                            data = json.load(f)

                        # If the JSON file is a JSON Schema file.
                        if any(field in data for field in ('$schema', 'definitions', 'properties')):
                            expected = deepcopy(data)
                            update_codelist_enum(data)

                            if expected != data:
                                with open(path, 'w') as f:
                                    json_dump(data, f, indent=2)
                                    f.write('\n')

        codelists = {}
        codelists_seen = set()
        meta_schema_exceptions = {
            'meta-schema.json',
            'meta-schema-patch.json',
        }

        if self.args.extension:
            collect_codelists(self.args.standard)
            codelists_seen = set(codelists)

            directories = self.args.extension
        else:
            directories = [self.args.standard]

        for directory in directories:
            collect_codelists(directory)
            update_json_schema(directory)

        codelists_not_seen = []
        for codelist in codelists.keys():
            if codelist not in codelists_seen:
                codelists_not_seen.append(codelist)

        if codelists_not_seen:
            logger.error('unused codelists: {}'.format(' '.join(codelists_not_seen)))
