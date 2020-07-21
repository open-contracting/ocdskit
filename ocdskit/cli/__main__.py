import argparse
import importlib
import logging
import sys
import warnings

import ijson

from ocdskit.exceptions import CommandError

logger = logging.getLogger('ocdskit')

COMMAND_MODULES = (
    'ocdskit.cli.commands.combine_record_packages',
    'ocdskit.cli.commands.combine_release_packages',
    'ocdskit.cli.commands.compile',
    'ocdskit.cli.commands.convert_to_oc4ids',
    'ocdskit.cli.commands.detect_format',
    'ocdskit.cli.commands.echo',
    'ocdskit.cli.commands.indent',
    'ocdskit.cli.commands.mapping_sheet',
    'ocdskit.cli.commands.package_records',
    'ocdskit.cli.commands.package_releases',
    'ocdskit.cli.commands.schema_report',
    'ocdskit.cli.commands.schema_strict',
    'ocdskit.cli.commands.set_closed_codelist_enums',
    'ocdskit.cli.commands.split_record_packages',
    'ocdskit.cli.commands.split_release_packages',
    'ocdskit.cli.commands.tabulate',
    'ocdskit.cli.commands.upgrade',
    'ocdskit.cli.commands.validate',
)


def main():
    parser = argparse.ArgumentParser(description='Open Contracting Data Standard CLI')
    parser.add_argument('--encoding', help='the file encoding')
    parser.add_argument('--ascii', help='print escape sequences instead of UTF-8 characters', action='store_true')
    parser.add_argument('--pretty', help='pretty print output', action='store_true')

    subparsers = parser.add_subparsers(dest='subcommand')

    subcommands = {}

    for module in COMMAND_MODULES:
        try:
            command = importlib.import_module(module).Command(subparsers)
        except ImportError as e:
            logger.error('exception "%s" prevented loading of %s module', e, module)
        else:
            subcommands[command.name] = command

    args = parser.parse_args()

    if args.subcommand:
        command = subcommands[args.subcommand]
        try:
            command.args = args
            try:
                with warnings.catch_warnings():
                    warnings.showwarning = _showwarning
                    command.handle()
            except ijson.common.IncompleteJSONError as e:
                if e.args and isinstance(e.args[0], (bytes, UnicodeDecodeError)):
                    message = e.args[0]
                    if isinstance(e.args[0], bytes):  # YAJL backends
                        message = e.args[0].decode(errors='backslashreplace')
                    _raise_encoding_error(message, args.encoding)
                raise CommandError('JSON error: {}'.format(e))
            except UnicodeDecodeError as e:
                _raise_encoding_error(e, args.encoding)
        except CommandError as e:
            logger.critical(e)
            sys.exit(1)
    else:
        parser.print_help()


def _showwarning(message, category, filename, lineno, file=None, line=None):
    if file is None:
        file = sys.stderr
    print(message, file=file)


def _raise_encoding_error(e, encoding):
    if encoding and encoding.lower() == 'iso-8859-1':
        suggestion = 'utf-8'
    else:
        suggestion = 'iso-8859-1'
    raise CommandError('encoding error: {}\nTry `--encoding {}`?'.format(e, suggestion))


if __name__ == '__main__':
    main()
