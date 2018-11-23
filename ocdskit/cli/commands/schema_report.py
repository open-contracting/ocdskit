import csv
import json
import sys
from collections import defaultdict
from operator import itemgetter


from .base import BaseCommand


class Command(BaseCommand):
    name = 'schema-report'
    help = 'reports details of a JSON Schema'

    def add_arguments(self):
        self.add_argument('--no-codelists', action='store_true',
                          help='skip reporting open and closed codelists')
        self.add_argument('--no-definitions', action='store_true',
                          help='skip reporting definitions that can use a common $ref in the versioned release schema')
        self.add_argument('--min-occurrences', type=int, default=5,
                          help='report definitions that occur at least this many times (default 5)')

    def handle(self):
        keywords_to_ignore = (
            # Metadata keywords
            # https://tools.ietf.org/html/draft-fge-json-schema-validation-00#section-6
            'title',
            'description',
            'default',

            # Extended keywords
            # http://os4d.opendataservices.coop/development/schema/#extended-json-schema
            'deprecated',
            'codelist',
            'openCodelist',
            'omitWhenMerged',
            'wholeListMerge',
            'versionId',
        )

        def recurse(data, pointer=''):
            if isinstance(data, list):
                for index, item in enumerate(data):
                    recurse(item, pointer='{}/{}'.format(pointer, index))
            elif isinstance(data, dict):
                parts = pointer.rsplit('/', 2)
                # Find item and property definitions that can use a common $ref in the versioned release schema.
                if len(parts) == 3 and (parts[-2] == 'properties' or parts[-1] == 'items') and '$ref' not in data:
                    # See http://standard.open-contracting.org/latest/en/schema/merging/#versioned-data
                    if parts[-1] != 'id' or 'versionId' in data:
                        definition = {k: data[k] for k in sorted(data) if k not in keywords_to_ignore}
                        definitions[repr(definition)] += 1

                if 'codelist' in data:
                    codelist = data['codelist']
                    # If the CSV file is used for open and closed codelists, treat it as closed.
                    if data['openCodelist']:
                        codelists[codelist].add('open')
                    else:
                        codelists[codelist].add('closed')

                for key, value in data.items():
                    recurse(value, pointer='{}/{}'.format(pointer, key))

        schema = json.load(self.buffer())

        codelists = defaultdict(set)
        definitions = defaultdict(int)
        recurse(schema)

        if not self.args.no_codelists:
            writer = csv.writer(sys.stdout, lineterminator='\n')
            writer.writerow(['codelist', 'openness'])
            for codelist, openness in sorted(codelists.items()):
                writer.writerow([codelist, '/'.join(sorted(openness))])

        if not self.args.no_codelists and not self.args.no_definitions:
            print()

        if not self.args.no_definitions:
            for definition, count in sorted(definitions.items(), key=itemgetter(1), reverse=True):
                if count < self.args.min_occurrences:
                    break
                print('{:2d}: {}'.format(count, definition))
