from collections import defaultdict, OrderedDict
from functools import lru_cache

import ocdsmerge

from .base import BaseCommand


@lru_cache()
def get_merge_rules(schema=None):
    return ocdsmerge.get_merge_rules(schema)


def make_compiled_release(releases, schema=None):
    return ocdsmerge.merge(releases, merge_rules=get_merge_rules(schema))


def make_versioned_release(releases, schema=None):
    return ocdsmerge.merge_versioned(releases, merge_rules=get_merge_rules(schema))


class Command(BaseCommand):
    name = 'compile'
    help = 'reads release packages from standard input, merges the releases by OCID, and prints the compiled releases'

    def add_arguments(self):
        self.add_argument('--package', action='store_true',
                          help='wrap the compiled releases in a record package')
        self.add_argument('--versioned', action='store_true',
                          help='if --package is set, include versioned releases in the record package; '
                               'otherwise, print versioned releases instead of compiled releases')

    def handle(self):
        if self.args.package:
            output = OrderedDict([('extensions', OrderedDict()), ('packages', []), ('records', [])])

        releases_by_ocid = defaultdict(list)

        for line in self.buffer():
            package = self.json_loads(line)

            for release in package['releases']:
                releases_by_ocid[release['ocid']].append(release)

            if self.args.package:
                self._update_package_metadata(output, package)

                output['packages'].append(package['uri'])

        if self.args.package:
            for ocid, releases in releases_by_ocid.items():
                record = OrderedDict([
                    ('ocid', ocid),
                    ('releases', releases),
                    ('compiledRelease', ocdsmerge.merge(releases)),
                ])

                if self.args.versioned:
                    record['versionedRelease'] = ocdsmerge.merge_versioned(releases)

                output['records'].append(record)

            self._set_extensions_metadata(output)

            self.print(output)
        else:
            for releases in releases_by_ocid.values():
                if self.args.versioned:
                    merge_method = make_versioned_release
                else:
                    merge_method = make_compiled_release

                merged_release = merge_method(releases)

                self.print(merged_release)
