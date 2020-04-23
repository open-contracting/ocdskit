import os
import sys

import ijson

from ocdskit.util import iterencode, json_dumps


class StandardInputReader:
    def __init__(self, encoding):
        self.encoding = encoding

    def read(self, buf_size):
        data = sys.stdin.buffer.read(buf_size)
        if self.encoding is None or self.encoding == 'utf-8':
            return data
        return data.decode(self.encoding).encode('utf-8')


class BaseCommand:
    kwargs = {}

    def __init__(self, subparsers):
        """
        Initializes the subparser and adds arguments.
        """
        self.subparser = subparsers.add_parser(self.name, description=self.help, **self.kwargs)
        self.add_base_arguments()
        self.add_arguments()

    def add_base_arguments(self):
        """
        Adds default arguments to all commands.
        """
        pass

    def add_arguments(self):
        """
        Adds arguments specific to this command.
        """
        pass

    def add_argument(self, *args, **kwargs):
        """
        Adds an argument to the subparser.
        """
        self.subparser.add_argument(*args, **kwargs)

    def handle(self):
        """
        Runs the command.
        """
        raise NotImplementedError('commands must implement handle()')

    def prefix(self):
        """
        Returns the path to the items to process within each input.
        """
        return ''

    def items(self, **kwargs):
        """
        Yields the items in the input.
        """
        file = StandardInputReader(self.args.encoding)
        yield from ijson.items(file, self.prefix(), multiple_values=True, **kwargs)

    def print(self, data, streaming=False):
        """
        Prints JSON data.

        :param bool streaming: whether to stream output using ``json.JSONEncoder().iterencode()`` (it is only more
            memory efficient if ``data`` contains iterators)
        """
        kwargs = {}
        if self.args.pretty:
            kwargs['indent'] = 2
        if self.args.ascii:
            kwargs['ensure_ascii'] = True

        try:
            if streaming:
                for chunk in iterencode(data, **kwargs):
                    print(chunk, end='')
                print()
            else:
                print(json_dumps(data, **kwargs))
            sys.stdout.flush()
        # https://docs.python.org/3/library/signal.html#note-on-sigpipe
        except BrokenPipeError:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            sys.exit(1)


class OCDSCommand(BaseCommand):
    def add_base_arguments(self):
        self.add_argument('--root-path', type=str, default='',
                          help='the path to the items to process within each input')

    def prefix(self):
        return self.args.root_path

    def items(self, **kwargs):
        """
        Yields the items in the input. If an item is an array, yields each entry of the array.
        """
        for item in super().items(**kwargs):
            if isinstance(item, list):
                for i in item:
                    yield i
            else:
                yield item

    def add_package_arguments(self, infix, prefix='', version='1.1'):
        """
        Adds arguments for setting package metadata to the subparser.
        """
        kwargs = {
            'infix': infix,
            'prefix': prefix,
        }

        template = "{prefix}set the {infix} package's {{}} to this value".format(**kwargs)

        self.add_argument('--uri', type=str, default='', help=template.format('uri'))
        self.add_argument('--published-date', type=str, default='', help=template.format('publishedDate'))
        self.add_argument('--version', type=str, default=version, help=template.format("version"))
        self.add_argument('--publisher-name', type=str, default='', help=template.format("publisher's name"))
        self.add_argument('--publisher-uri', type=str, default='', help=template.format("publisher's uri"))
        self.add_argument('--publisher-scheme', type=str, default='', help=template.format("publisher's scheme"))
        self.add_argument('--publisher-uid', type=str, default='', help=template.format("publisher's uid"))
        self.add_argument('--fake', action='store_true',
                          help="{prefix}set the {infix} package's required metadata to dummy values".format(**kwargs))

    def parse_package_arguments(self):
        """
        Returns package metadata as a dictionary to be used as keyword arguments.
        """
        kwargs = {
            'uri': self.args.uri,
            'publisher': {},
            'published_date': self.args.published_date,
            'version': self.args.version,
        }

        if self.args.fake:
            if not kwargs['uri']:
                kwargs['uri'] = 'placeholder:'
            if not kwargs['published_date']:
                kwargs['published_date'] = '9999-01-01T00:00:00Z'

        for key in ('publisher_name', 'publisher_uri', 'publisher_scheme', 'publisher_uid'):
            value = getattr(self.args, key)
            if value:
                kwargs['publisher'][key[10:]] = value

        return kwargs
