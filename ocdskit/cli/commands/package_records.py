from ocdskit.cli.commands.base import OCDSCommand
from ocdskit.combine import package_records
from ocdskit.util import grouper


class Command(OCDSCommand):
    name = 'package-records'
    help = 'reads records from standard input, and prints one record package'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')
        self.add_argument('--size', type=int, help='the maximum number of records per package')

        self.add_package_arguments('record')

    def handle(self):
        kwargs = self.parse_package_arguments()
        kwargs['extensions'] = self.args.extension

        if self.args.size:  # assume `--size` is reasonable
            for data in grouper(self.items(), self.args.size):
                output = package_records(list(filter(None, data)), **kwargs)
                self.print(output)
        else:
            output = package_records(self.items(), **kwargs)
            self.print(output, streaming=True)
