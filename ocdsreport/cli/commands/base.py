import json
import io
import sys

from ocdskit.exceptions import CommandError


class BaseCommand(object):
    def __init__(self, subparsers):
        self.subparser = subparsers.add_parser(self.name, description=self.help)
        self.add_arguments()

    def add_arguments(self):
        pass

    def add_argument(self, *args, **kwargs):
        self.subparser.add_argument(*args, **kwargs)

    def read(self, encoding):
        try:
            return json.loads(io.TextIOWrapper(sys.stdin.buffer, encoding=encoding).read())
        except UnicodeDecodeError as e:
            if encoding and encoding.lower() == 'iso-8859-1':
                suggestion = 'utf-8'
            else:
                suggestion = 'iso-8859-1'
            raise CommandError('encoding error: try `--encoding {}`? ({})'.format(suggestion, e))

    def handle(self, args, data):
        raise NotImplementedError('commands must implement handle(args, data)')
