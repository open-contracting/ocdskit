import csv
import os.path
import pathlib
import sys
from collections import defaultdict
from operator import itemgetter

import jsonref

from ocdskit.cli.commands.base import BaseCommand


class Command(BaseCommand):
    name = 'schema-report'
    help = 'reports details of a JSON Schema'

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--no-codelists', action='store_true', help='skip reporting open and closed codelists')
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
            'omitWhenMerged',
            'wholeListMerge',
            'versionId',
        )

        def add_definition(data):
            if '$ref' not in data:
                definition = {k: v for k, v in sorted(data.items()) if k not in keywords_to_ignore}
                definitions[repr(definition)] += 1

        def recurse(data):
            if isinstance(data, list):
                for item in data:
                    recurse(item)
            elif isinstance(data, dict):
                if 'codelist' in data:
                    if 'openCodelist' in data:
                        open_codelist = data['openCodelist']
                    else:
                        open_codelist = 'enum' not in data
                    codelists[data['codelist']].add(open_codelist)

                for key, value in data.items():
                    # Find definitions that can use a common $ref in the versioned release schema. Unversioned fields,
                    # like the `id`'s of objects in arrays that are not `wholeListMerge`, should be excluded, but it's
                    # too much work with too little advantage to do so.
                    if key in ('definitions', 'properties'):
                        for k, v in value.items():
                            add_definition(v)
                    recurse(value)

        with open(self.args.file) as f:
            schema = jsonref.load(f, base_uri=pathlib.Path(os.path.realpath(self.args.file)).as_uri())

        codelists = defaultdict(set)
        definitions = defaultdict(int)
        recurse(schema)

        if not self.args.no_codelists:
            writer = csv.writer(sys.stdout, lineterminator='\n')
            writer.writerow(['codelist', 'openCodelist'])
            for codelist, openness in sorted(codelists.items()):
                writer.writerow([codelist, '/'.join(str(value) for value in sorted(openness))])

        if not self.args.no_codelists and not self.args.no_definitions:
            print()

        if not self.args.no_definitions:
            for definition, count in sorted(definitions.items(), key=itemgetter(1), reverse=True):
                if count < self.args.min_occurrences:
                    break
                print('{:2d}: {}'.format(count, definition))
