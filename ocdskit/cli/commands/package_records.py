from ocdskit.cli.commands.base import OCDSCommand
from ocdskit.combine import package_records


class Command(OCDSCommand):
    name = 'package-records'
    help = 'reads records from standard input, and prints one record package'

    def add_arguments(self):
        self.add_argument('extension', help='add this extension to the package', nargs='*')

        self.add_package_arguments('record')

    def handle(self):
        kwargs = self.parse_package_arguments()
        kwargs['extensions'] = self.args.extension

        output = package_records(list(self.items()), **kwargs)

        self.print(output)
