from collections import OrderedDict

from .base import BaseCommand


class Command(BaseCommand):
    name = 'combine-record-packages'
    help = 'reads record packages from standard input, collects packages and records, and prints one record package'

    def handle(self):
        output = OrderedDict([('extensions', OrderedDict()), ('packages', []), ('records', [])])

        for line in self.buffer():
            package = self.json_loads(line)

            self._update_package_metadata(output, package)

            output['records'].extend(package['records'])

            if 'packages' in package:
                output['packages'].extend(package['packages'])

        if not output['packages']:
            del output['packages']

        self._set_extensions_metadata(output)

        self.print(output)
