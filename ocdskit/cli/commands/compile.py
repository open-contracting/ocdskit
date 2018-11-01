from collections import defaultdict
from datetime import datetime

import ocdsmerge

from .base import BaseCommand


class Command(BaseCommand):
    name = 'compile'
    help = 'reads release packages from standard input, merges the releases by OCID, and prints the compiled releases'

    def add_arguments(self):
        self.add_argument('extension', nargs='*',
                          help='if --package is set, add this extension to the package')
        self.add_argument('--package', action='store_true',
                          help='wrap the compiled releases in a record package '
                               '(you will need to edit the package metadata)')
        self.add_argument('--versioned', action='store_true',
                          help='if --package is set, include versioned releases in the record package; '
                               'otherwise, print versioned releases instead of compiled releases')

    def handle(self):
        if self.args.extension and not self.args.package:
            self.subparser.error('You must use --package with extension positional arguments.')

        releases_by_ocid = defaultdict(list)

        for line in self.buffer():
            release_package = self.json_loads(line)
            for release in release_package['releases']:
                releases_by_ocid[release['ocid']].append(release)

        if self.args.package:
            records = []
            for ocid, releases in releases_by_ocid.items():
                record = {
                    'ocid': ocid,
                    'releases': releases,
                    'compiledRelease': ocdsmerge.merge(releases),
                }
                if self.args.versioned:
                    record['versionedRelease'] = ocdsmerge.merge_versioned(releases)
                records.append(record)

            self.print({
                'uri': 'http://example.com',
                'publisher': {
                    'name': '',
                },
                'publishedDate': datetime.utcnow().date().isoformat() + 'T00:00:00Z',
                'version': '1.1',
                'extensions': self.args.extension,
                'records': records,
            })
        else:
            for releases in releases_by_ocid.values():
                if self.args.versioned:
                    merge_method = ocdsmerge.merge_versioned
                else:
                    merge_method = ocdsmerge.merge
                merged_release = merge_method(releases)
                self.print(merged_release)
