from ocdskit.cli.commands.base import OCDSCommand
from ocdskit.combine import package_releases
from ocdskit.util import grouper


class Command(OCDSCommand):
    name = 'package-releases'
    help = 'reads releases from standard input, and prints one release package'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')
        self.add_argument('--size', type=int, help='the maximum number of releases per package')

        self.add_package_arguments('release')

    def handle(self):
        kwargs = self.parse_package_arguments()
        kwargs['extensions'] = self.args.extension

        if self.args.size:  # assume `--size` is reasonable
            for data in grouper(self.items(), self.args.size):
                output = package_releases(list(filter(None, data)), **kwargs)
                self.print(output)
        else:
            output = package_releases(self.items(), **kwargs)
            self.print(output, streaming=True)
