import logging
import sys

import ocdskit.packager
from ocdskit.cli.commands.base import OCDSCommand
from ocdskit.combine import merge
from ocdskit.exceptions import CommandError, InconsistentVersionError, MissingOcidKeyError

logger = logging.getLogger('ocdskit')


class Command(OCDSCommand):
    name = 'compile'
    help = 'reads release packages and individual releases from standard input, merges the releases by OCID, and ' \
           'prints the compiled releases'

    def add_arguments(self):
        self.add_argument('--schema', help='the URL or path of the patched release schema to use')
        self.add_argument('--package', action='store_true', help='wrap the compiled releases in a record package')
        self.add_argument('--linked-releases', action='store_true',
                          help='if --package is set, use linked releases instead of full releases')
        self.add_argument('--versioned', action='store_true',
                          help='if --package is set, include versioned releases in the record package; otherwise, '
                               'print versioned releases instead of compiled releases')

        self.add_package_arguments('record', 'if --package is set, ')

    def handle(self):
        kwargs = self.parse_package_arguments()
        kwargs['schema'] = self.args.schema
        kwargs['return_package'] = self.args.package
        kwargs['use_linked_releases'] = self.args.linked_releases
        kwargs['return_versioned_release'] = self.args.versioned

        if not ocdskit.packager.using_sqlite:
            logger.warning('sqlite3 is unavailable, so the command will run in memory. If input files are too large, '
                           'the command might exceed available memory.')

        try:
            for output in merge(self.items(), streaming=True, **kwargs):
                self.print(output, streaming=self.args.package)
        except MissingOcidKeyError:
            raise CommandError('The `ocid` field of at least one release is missing.')
        except InconsistentVersionError as e:
            versions = [e.earlier_version, e.current_version]
            if versions[1] < versions[0]:
                versions.reverse()

            raise CommandError('{}\nTry first upgrading items to the same version:\n  cat file [file ...] | ocdskit '
                               'upgrade {}:{} | ocdskit compile {}'.format(str(e), *versions, ' '.join(sys.argv[2:])))
