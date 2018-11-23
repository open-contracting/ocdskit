import json
from collections import defaultdict
from operator import itemgetter


from .base import BaseCommand


class Command(BaseCommand):
    name = 'schema-report'
    help = 'reports details of a JSON Schema (open and closed codelists)'

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
                if len(parts) == 3 and parts[-2] in ('items', 'properties') and '$ref' not in data:
                    # See http://standard.open-contracting.org/latest/en/schema/merging/#versioned-data
                    if parts[-1] != 'id' or 'versionId' in data:
                        definition = {k: data[k] for k in sorted(data) if k not in keywords_to_ignore}
                        definitions[repr(definition)] += 1

                if 'codelist' in data:
                    codelist = data['codelist']
                    # If the CSV file is used for open and closed codelists, treat it as closed.
                    if codelist not in codelists:
                        codelists[codelist] = data['openCodelist']
                    elif not data['openCodelist']:
                        codelists[codelist] = data['openCodelist']

                for key, value in data.items():
                    recurse(value, pointer='{}/{}'.format(pointer, key))

        schema = json.load(self.buffer())

        codelists = {}
        definitions = defaultdict(int)
        recurse(schema)

        partitioned_codelists = {
            True: set(),
            False: set(),
        }

        for codelist, open_codelist in codelists.items():
            partitioned_codelists[open_codelist].add(codelist)

        for open_codelist, codelists in partitioned_codelists.items():
            if codelists:
                print('openCodelist: {}\n{}\n'.format(open_codelist, '\n'.join(sorted(codelists))))

        for definition, count in sorted(definitions.items(), key=itemgetter(1), reverse=True):
            if count <= 2:
                break
            print('{:2d}: {}'.format(count, definition))
