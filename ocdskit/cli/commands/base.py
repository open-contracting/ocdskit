import json
import io
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

    def json_load(self, io):
        """
        Parses JSON from a stream.
        """
        return json.load(io, object_pairs_hook=OrderedDict)

    def json_loads(self, data):
        """
        Parses JSON from a string.
        """
        return json.loads(data, object_pairs_hook=OrderedDict)

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

    def _update_package_metadata(self, output, package):
        if 'publisher' in package:
            output['publisher'] = package['publisher']

        if 'extensions' in package:
            # Python has no OrderedSet, so we use OrderedDict to keep extensions in order without duplication.
            output['extensions'].update(OrderedDict.fromkeys(package['extensions']))

        for field in ('license', 'publicationPolicy', 'version'):
            if field in package:
                output[field] = package[field]

    def _set_extensions_metadata(self, output):
        if output['extensions']:
            output['extensions'] = list(output['extensions'])
        else:
            del output['extensions']

    def _remove_empty_optional_metadata(self, output):
        for field in ('license', 'publicationPolicy', 'version'):
            if output[field] is None:
                del output[field]
