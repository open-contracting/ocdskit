import logging
import os.path

import ijson

from ocdskit.cli.commands.base import OCDSCommand
from ocdskit.exceptions import UnknownFormatError

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
                for root, dirs, files in os.walk(file):
                    for name in files:
                        if not name.startswith('.'):
                            self.detect_format(os.path.join(root, name))
            elif os.path.isdir(file):
                logger.warning('{} is a directory. Set --recursive to recurse into directories.'.format(file))
            else:
                logger.error('{}: No such file or directory'.format(file))

    def detect_format(self, path):
        try:
            with open(path, 'rb') as f:
                events = iter(ijson.parse(f, multiple_values=True))

                while True:
                    prefix, event, value = next(events)
                    if prefix == self.args.root_path:
                        break

                if prefix:
                    prefix += '.'

                if event == 'start_array':
                    prefix += 'item.'
                elif event != 'start_map':
                    raise UnknownFormatError('top-level JSON value is a {}'.format(event))

                records_prefix = '{}records'.format(prefix)
                releases_prefix = '{}releases'.format(prefix)
                ocid_prefix = '{}ocid'.format(prefix)
                tag_item_prefix = '{}tag.item'.format(prefix)

                has_records = False
                has_releases = False
                has_ocid = False
                has_tag = False
                is_compiled = False
                is_array = event == 'start_array'

                for prefix, event, value in events:
                    if prefix == records_prefix:
                        has_records = True
                    elif prefix == releases_prefix:
                        has_releases = True
                    elif prefix == ocid_prefix:
                        has_ocid = True
                    elif prefix == tag_item_prefix:
                        has_tag = True
                        if value == 'compiled':
                            is_compiled = True
                    if not prefix and event not in ('end_array', 'end_map', 'map_key'):
                        return _print(path, True, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled)

                return _print(path, False, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled)
        except UnknownFormatError as e:
            logger.warning('{}: unknown ({})'.format(path, e))


def _print(path, is_concatenated, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled):
    if has_records:
        string = 'record package'
    elif has_releases and has_ocid:
        string = 'record'
    elif has_releases:
        string = 'release package'
    elif is_compiled:
        string = 'compiled release'
    elif has_tag:
        string = 'release'
    elif has_ocid:
        string = 'versioned release'
    else:
        if is_array:
            infix = 'array'
        else:
            infix = 'object'
        raise UnknownFormatError('top-level JSON value is a non-OCDS {}'.format(infix))

    if is_array:
        string = 'a JSON array of {}s'.format(string)

    if is_concatenated:
        string = 'concatenated JSON, starting with {}'.format(string)

    print('{}: {}'.format(path, string))
