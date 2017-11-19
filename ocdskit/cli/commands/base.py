import json
import io
import sys


class BaseCommand(object):
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

        print(json.dumps(data, **kwargs))
