from collections import OrderedDict

from .base import BaseCommand


class Command(BaseCommand):
    name = 'combine-release-packages'
    help = 'reads release packages from standard input, collects releases, and prints one release package'

    def add_arguments(self):
        self.add_argument('--uri', type=str,
                          help="set the release package's uri to this value")
        self.add_argument('--published-date', type=str,
                          help="set the release package's publishedDate to this value")

    def handle(self):
        output = OrderedDict([
            ('uri', self.args.uri),
            ('publisher', OrderedDict()),
            ('publishedDate', self.args.published_date),
            ('license', None),
            ('publicationPolicy', None),
            ('version', None),
            ('extensions', OrderedDict()),
            ('releases', []),
        ])

        for line in self.buffer():
            package = self.json_loads(line)

            self._update_package_metadata(output, package)

            output['releases'].extend(package['releases'])

        self._set_extensions_metadata(output)
        self._remove_empty_optional_metadata(output)

        self.print(output)
