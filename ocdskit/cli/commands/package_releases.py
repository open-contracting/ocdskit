from collections import OrderedDict

from .base import BaseCommand


class Command(BaseCommand):
    name = 'package-releases'
    help = 'reads releases from standard input, and prints one release package ' \
           '(you will need to edit the package metadata)'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')

    def handle(self):
        releases = [self.json_loads(line) for line in self.buffer()]

        self.print(OrderedDict([
            ('uri', 'http://example.com'),
            ('publisher', {'name': ''}),
            ('publishedDate', '9999-01-01T00:00:00Z'),
            ('version', '1.1'),
            ('extensions', self.args.extension),
            ('releases', releases),
        ]))
