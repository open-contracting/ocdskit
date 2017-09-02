import json

import ocdsmerge

from .base import BaseCommand


class Command(BaseCommand):
    name = 'compile'
    help = "compile the release packages' releases"

    def handle(self, args, data):
        if isinstance(data, dict):
            data = [data]

        compiled_releases = [ocdsmerge.merge(release_package['releases']) for release_package in data]

        print(json.dumps(compiled_releases, indent=2, separators=(',', ': ')))
