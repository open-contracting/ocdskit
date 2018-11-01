from datetime import datetime

from .base import BaseCommand


class Command(BaseCommand):
    name = 'release-package'
    help = 'reads releases from standard input, and prints one release package'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')

    def handle(self):
        releases = [self.json_loads(line) for line in self.buffer()]

        self.print({
            "uri": "http://example.com",
            "publisher": {
                "name": ""
            },
            "publishedDate": datetime.utcnow().date().isoformat() + 'T00:00:00Z',
            "version": "1.1",
            "extensions": self.args.extension,
            "releases": releases,
        })
