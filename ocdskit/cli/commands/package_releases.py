from .base import OCDSCommand
from ocdskit.combine import package_releases


class Command(OCDSCommand):
    name = 'package-releases'
    help = 'reads releases from standard input, and prints one release package'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')

        self.add_package_arguments('release')

    def handle(self):
        kwargs = self.parse_package_arguments()
        kwargs['extensions'] = self.args.extension

        output = package_releases(list(self.items()), **kwargs)

        self.print(output)
