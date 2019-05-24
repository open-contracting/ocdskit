import io
import json
import sys
from collections import OrderedDict


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

    def buffer(self):
        return io.TextIOWrapper(sys.stdin.buffer, encoding=self.args.encoding)

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

        print(json.dumps(data, **kwargs))

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
            if value:
                metadata['publisher'][key[10:]] = value

        return metadata
