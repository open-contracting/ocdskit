import json

import ocdsmerge

from .base import BaseCommand


class Command(BaseCommand):
    name = 'compile'
    help = "compile a release package's releases"

    def handle(self):
        """
        Reads a release package from standard input, merges its releases, and prints the compiled release.
        """
        for line in self.buffer():
            release_package = json.loads(line)
            compiled_release = ocdsmerge.merge(release_package['releases'])
            self.print(compiled_release, self.args.pretty)
