import logging
import sys

from .base import OCDSCommand
from ocdskit.combine import compile_release_packages
from ocdskit.exceptions import CommandError, InconsistentVersionError

logger = logging.getLogger('ocdskit')


class Command(OCDSCommand):
    name = 'compile'
    help = 'reads release packages from standard input, merges the releases by OCID, and prints the compiled releases'

    def add_arguments(self):
        self.add_argument('--schema', help='the URL or path of the release schema to use')
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

        try:
            for output in compile_release_packages(self.items(), **kwargs):
                self.print(output)
        except InconsistentVersionError as e:
            versions = [e.earlier_version, e.current_version]
            if versions[1] < versions[0]:
                versions.reverse()

            raise CommandError('{}\nTry first upgrading packages to the same version:\n  cat file [file ...] | ocdskit'
                               ' upgrade {}:{} | ocdskit compile {}'.format(str(e), *versions, ' '.join(sys.argv[2:])))
