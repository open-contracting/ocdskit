from collections import OrderedDict

from .base import BaseCommand


class Command(BaseCommand):
    name = 'combine-release-packages'
    help = 'reads release packages from standard input, collects releases, and prints one release package'

    def handle(self):
        output = OrderedDict([('extensions', OrderedDict()), ('releases', [])])

        for line in self.buffer():
            package = self.json_loads(line)

            self._update_package_metadata(output, package)

            output['releases'].extend(package['releases'])

        self._set_extensions_metadata(output)

        self.print(output)
