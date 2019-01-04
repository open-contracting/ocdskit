from collections import OrderedDict

from .base import BaseCommand


class Command(BaseCommand):
    name = 'combine-record-packages'
    help = 'reads record packages from standard input, collects packages and records, and prints one record package'

    def add_arguments(self):
        self.add_argument('--uri', type=str,
                          help="set the record package's uri to this value")
        self.add_argument('--published-date', type=str,
                          help="set the record package's publishedDate to this value")

    def handle(self):
        output = OrderedDict([
            ('uri', self.args.uri),
            ('publisher', OrderedDict()),
            ('publishedDate', self.args.published_date),
            ('license', None),
            ('publicationPolicy', None),
            ('version', None),
            ('extensions', OrderedDict()),
            ('packages', []),
            ('records', []),
        ])

        for line in self.buffer():
            package = self.json_loads(line)

            self._update_package_metadata(output, package)

            output['records'].extend(package['records'])

            if 'packages' in package:
                output['packages'].extend(package['packages'])

        if not output['packages']:
            del output['packages']

        self._set_extensions_metadata(output)
        self._remove_empty_optional_metadata(output)

        self.print(output)
