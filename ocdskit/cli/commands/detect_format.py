import logging
import os.path

from .base import ijson, OCDSCommand
from ocdskit.exceptions import UnknownFormatError

logger = logging.getLogger('ocdskit')


class Command(OCDSCommand):
    name = 'detect-format'
    help = 'reads OCDS files, and reports whether each is a release, record, package, etc.'

    def add_arguments(self):
        self.add_argument('file', help='OCDS files', nargs='+')

    def handle(self):
        for file in self.args.file:
            if os.path.isfile(file):
                try:
                    result = self.detect_format(file)
                    print('{}: {}'.format(file, result))
                except UnknownFormatError as e:
                    logger.warning('{}: unknown ({})'.format(file, e))
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
        with open(path, 'rb') as f:
            events = iter(ijson.parse(f, multiple_values=True))

            prefix, event, value = next(events)
            if event == 'start_array':
                is_array = True
                prefix = 'item.'
            elif event == 'start_map':
                is_array = False
                prefix = ''
            else:
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
                if not prefix and event in ('start_array', 'start_map'):
                    return self.array_format(True, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled)

            return self.array_format(False, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled)

    def array_format(self, is_concatenated, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled):
        if has_records:
            string = 'record package'
        elif has_releases and not has_ocid:
            string = 'release package'
        elif has_releases:
            string = 'record'
        elif is_compiled:
            string = 'compiled release'
        elif has_tag:
            string = 'release'
        else:
            string = 'versioned release'

        if is_array:
            string = 'a JSON array of {}s'.format(string)

        if is_concatenated:
            string = 'concatenated JSON, starting with {}'.format(string)

        return string
