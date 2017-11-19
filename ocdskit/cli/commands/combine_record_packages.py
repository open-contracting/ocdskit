import json
from datetime import datetime

from .base import BaseCommand


class Command(BaseCommand):
    name = 'combine-record-packages'
    help = 'reads record packages from standard input, collects packages and records, and prints one record package'

    def handle(self):
        output = {'packages': [], 'records': []}

        for line in self.buffer():
            package = json.loads(line)

            # Use sample metadata.
            output['uri'] = package['uri']
            output['publishedDate'] = package['publishedDate']
            output['publisher'] = package['publisher']

            if 'extensions' in package:
                output['extensions'].update(package['extensions'])

            for field in ('license', 'publicationPolicy', 'version'):
                if field in package:
                    output[field] = package[field]

            for field in ('packages', 'records'):
                if package[field]:
                    output[field].extend(package[field])

        if not output['packages']:
            del output['packages']

        self.print(output)
