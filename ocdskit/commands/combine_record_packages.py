from ocdskit.combine import combine_record_packages
from ocdskit.commands.base import OCDSCommand


class Command(OCDSCommand):
    name = 'combine-record-packages'
    help = 'reads record packages from standard input, collects packages and records, and prints one record package'

    def add_arguments(self):
        self.add_package_arguments('record')

    def handle(self):
        kwargs = self.parse_package_arguments()

        output = combine_record_packages(self.items(), **kwargs)

        self.print(output)
