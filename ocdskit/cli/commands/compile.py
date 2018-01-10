import json
from collections import defaultdict, OrderedDict

import ocdsmerge

from .base import BaseCommand


class Command(BaseCommand):
    name = 'compile'
    help = 'reads release packages from standard input, merges the releases by OCID, and prints the compiled releases'

    def handle(self):
        releases_by_ocid = defaultdict(list)

        for line in self.buffer():
            release_package = json.loads(line, object_pairs_hook=OrderedDict)
            for release in release_package['releases']:
                releases_by_ocid[release['ocid']].append(release)

        for releases in releases_by_ocid.values():
            compiled_release = ocdsmerge.merge(releases)
            self.print(compiled_release)
