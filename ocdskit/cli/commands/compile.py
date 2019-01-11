import logging
import sys
from collections import defaultdict, OrderedDict

from ocdsmerge.merge import merge, merge_versioned, get_tags, get_release_schema_url

from .base import BaseCommand
from ocdskit.exceptions import CommandError
from ocdskit.util import get_ocds_minor_version

logger = logging.getLogger('ocdskit')


class Command(BaseCommand):
    name = 'compile'
    help = 'reads release packages from standard input, merges the releases by OCID, and prints the compiled releases'

    def add_arguments(self):
        self.add_argument('--schema',
                          help='the URL or path of the release schema to use')
        self.add_argument('--package', action='store_true',
                          help='wrap the compiled releases in a record package')
        self.add_argument('--uri', type=str,
                          help="if --package is set, set the record package's uri to this value")
        self.add_argument('--published-date', type=str,
                          help="if --package is set, set the record package's publishedDate to this value")
        self.add_argument('--linked-releases', action='store_true',
                          help='if --package is set, use linked releases instead of full releases')
        self.add_argument('--versioned', action='store_true',
                          help='if --package is set, include versioned releases in the record package; otherwise, '
                               'print versioned releases instead of compiled releases')

    def handle(self):
        if self.args.package:
            output = OrderedDict([
                ('uri', self.args.uri),
                ('publisher', OrderedDict()),
                ('publishedDate', self.args.published_date),
                ('license', None),
                ('publicationPolicy', None),
                ('version', None),
                ('extensions', OrderedDict()),
                ('packages', []),
                ('records', []),
            ])

        schema = self.args.schema
        version = None
        releases_by_ocid = defaultdict(list)
        linked_releases = []

        for i, line in enumerate(self.buffer()):
            package = self.json_loads(line)

            if not version:
                version = get_ocds_minor_version(package)
            else:
                current = get_ocds_minor_version(package)
                if current != version:
                    versions = [version, current]
                    if current < version:
                        versions.reverse()
                    raise CommandError('item {}: version error: this package uses version {}, but earlier packages '
                                       'used version {}\nTry upgrading packages to the same version:\n  cat file '
                                       '[file ...] | ocdskit upgrade {}:{} | ocdskit compile {}'.format(
                                            i, current, version, *versions, ' '.join(sys.argv[2:])))

            if not schema:
                prefix = version.replace('.', '__') + '__'
                tag = next(tag for tag in reversed(get_tags()) if tag.startswith(prefix))
                schema = get_release_schema_url(tag)

            for release in package['releases']:
                releases_by_ocid[release['ocid']].append(release)

                if self.args.package and self.args.linked_releases:
                    linked_releases.append(OrderedDict([
                        ('url', package['uri'] + '#' + release['id']),
                        ('date', release['date']),
                        ('tag', release['tag']),
                    ]))

            if self.args.package:
                self._update_package_metadata(output, package)

                output['packages'].append(package['uri'])

        if self.args.package:
            for ocid, releases in releases_by_ocid.items():
                record = OrderedDict([
                    ('ocid', ocid),
                    ('releases', []),
                    ('compiledRelease', merge(releases, schema)),
                ])

                if self.args.linked_releases:
                    record['releases'] = linked_releases
                else:
                    record['releases'] = releases

                if self.args.versioned:
                    record['versionedRelease'] = merge_versioned(releases, schema)

                output['records'].append(record)

            self._set_extensions_metadata(output)
            self._remove_empty_optional_metadata(output)

            self.print(output)
        else:
            for releases in releases_by_ocid.values():
                if self.args.versioned:
                    merge_method = merge_versioned
                else:
                    merge_method = merge

                merged_release = merge_method(releases, schema)

                self.print(merged_release)
