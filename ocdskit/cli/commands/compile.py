import json
from collections import defaultdict, OrderedDict

import ocdsmerge

from .base import BaseCommand


class Command(BaseCommand):
    name = 'compile'
    help = 'reads release packages from standard input, merges the releases by OCID, and prints the compiled releases'

    def add_arguments(self):
        self.add_argument('-V', '--versioned', help='print versioned releases', action='store_true')

    def handle(self):
        releases_by_ocid = defaultdict(list)

        for line in self.buffer():
            release_package = json.loads(line, object_pairs_hook=OrderedDict)
            for release in release_package['releases']:
                releases_by_ocid[release['ocid']].append(release)

        for releases in releases_by_ocid.values():
            if self.args.versioned:
                merge_method = ocdsmerge.merge_versioned
            else:
                merge_method = ocdsmerge.merge
            merged_release = merge_method(releases)
            self.print(merged_release)
