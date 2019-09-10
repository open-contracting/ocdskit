from .base import BaseCommand
from ocdskit.combine import combine_record_packages
from ocdskit.util import json_loads


class Command(BaseCommand):
    name = 'combine-record-packages'
    help = 'reads record packages from standard input, collects packages and records, and prints one record package'

    def add_arguments(self):
        self.add_package_arguments('record')

    def handle(self):
        kwargs = self.parse_package_arguments()

        packages = [json_loads(line) for line in self.buffer()]
        output = combine_record_packages(packages, **kwargs)

        self.print(output)
