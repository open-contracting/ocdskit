from .base import BaseCommand
from ocdskit.combine import package_releases
from ocdskit.util import json_loads


class Command(BaseCommand):
    name = 'package-releases'
    help = 'reads releases from standard input, and prints one release package'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')

        self.add_package_arguments('release')

    def handle(self):
        kwargs = self.parse_package_arguments()
        kwargs['extensions'] = self.args.extension

        releases = [json_loads(line) for line in self.buffer()]
        output = package_releases(releases, **kwargs)

        self.print(output)
