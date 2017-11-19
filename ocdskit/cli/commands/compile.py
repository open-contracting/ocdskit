import json

import ocdsmerge

from .base import BaseCommand


class Command(BaseCommand):
    name = 'compile'
    help = 'reads a release package from standard input, merges its releases, and prints the compiled release'

    def handle(self):
        # This assumes the releases in the release package are for one contracting process.
        for line in self.buffer():
            release_package = json.loads(line)
            compiled_release = ocdsmerge.merge(release_package['releases'])
            self.print(compiled_release)
