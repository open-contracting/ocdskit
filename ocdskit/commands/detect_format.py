import logging
import os.path

from ocdskit.commands.base import OCDSCommand
from ocdskit.exceptions import UnknownFormatError
from ocdskit.util import detect_format

logger = logging.getLogger('ocdskit')


class Command(OCDSCommand):
    name = 'detect-format'
    help = 'reads OCDS files, and reports whether each is a release, record, package, etc.'

    def add_arguments(self):
        self.add_argument('file', help='OCDS files', nargs='+')
        self.add_argument('-r', '--recursive', help='recursively indent JSON files', action='store_true')

    def handle(self):
        for file in self.args.file:
            if os.path.isfile(file):
                self.detect_format(file)
            elif self.args.recursive:
                for root, _, files in os.walk(file):
                    for name in files:
                        if not name.startswith('.'):
                            self.detect_format(os.path.join(root, name))
            elif os.path.isdir(file):
                logger.warning('%s is a directory. Set --recursive to recurse into directories.', file)
            else:
                logger.error('%s: No such file or directory', file)

    def detect_format(self, path):
        try:
            _print(path, *detect_format(path, self.args.root_path))
        except UnknownFormatError as e:
            logger.warning('%s: unknown (%s)', path, e)


def _print(path, detected_format, is_concatenated, is_array):
    string = detected_format

    if is_array:
        string = f'a JSON array of {string}s'

    if is_concatenated:
        string = f'concatenated JSON, starting with {string}'

    print(f'{path}: {string}')
