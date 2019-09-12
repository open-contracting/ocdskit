import sys
from collections import OrderedDict

from ocdskit.util import json_dumps

try:
    # ijson 2.4 has a bug in yajl2_c (fixed in HEAD).
    import ijson.backends.yajl2_cffi as ijson
except ijson.backends.YAJLImportError:
    import ijson


class StandardInputReader:
    def __init__(self, encoding):
        self.encoding = encoding

    def read(self, buf_size):
        data = sys.stdin.buffer.read(buf_size)
        if self.encoding is None or self.encoding == 'utf-8':
            return data
        return data.decode(self.encoding).encode('utf-8')


class BaseCommand:
    def __init__(self, subparsers):
        """
        Initializes the subparser and adds arguments.
        """
        self.subparser = subparsers.add_parser(self.name, description=self.help)
        self.add_arguments()

    def add_arguments(self):
        pass

    def add_argument(self, *args, **kwargs):
        """
        Adds an argument to the subparser.
        """
        self.subparser.add_argument(*args, **kwargs)

    def handle(self):
        raise NotImplementedError('commands must implement handle()')

    def items(self):
        return ijson.common.items(ijson.parse(StandardInputReader(self.args.encoding), multiple_values=True), '')

    def print(self, data):
        """
        Prints JSON data.
        """
        # See https://docs.python.org/2/library/json.html
        if self.args.pretty:
            kwargs = {'indent': 2, 'separators': (',', ': ')}
        else:
            kwargs = {'separators': (',', ':')}
        if not self.args.ascii:
            kwargs['ensure_ascii'] = False

        print(json_dumps(data, **kwargs))

    def add_package_arguments(self, infix, prefix=''):
        """
        Adds arguments for setting package metadata to the subparser.
        """
        template = "{prefix}set the {infix} package's {{}} to this value".format(infix=infix, prefix=prefix)

        self.add_argument('--uri', type=str,
                          help=template.format('uri'))
        self.add_argument('--published-date', type=str,
                          help=template.format('publishedDate'))
        self.add_argument('--publisher-name', type=str,
                          help=template.format("publisher's name"))
        self.add_argument('--publisher-uri', type=str,
                          help=template.format("publisher's uri"))
        self.add_argument('--publisher-scheme', type=str,
                          help=template.format("publisher's scheme"))
        self.add_argument('--publisher-uid', type=str,
                          help=template.format("publisher's uid"))

    def parse_package_arguments(self):
        """
        Returns a publisher block as a dictionary.
        """
        metadata = {
            'uri': self.args.uri,
            'publisher': OrderedDict(),
            'published_date': self.args.published_date,
        }

        for key in ('publisher_name', 'publisher_uri', 'publisher_scheme', 'publisher_uid'):
            value = getattr(self.args, key)
            if value is not None:
                metadata['publisher'][key[10:]] = value

        return metadata
