import argparse
import importlib
import logging
import sys
import warnings

from ocdskit.exceptions import CommandError
from ocdskit.util import ijson

logger = logging.getLogger('ocdskit')

COMMAND_MODULES = (
    'ocdskit.commands.combine_record_packages',
    'ocdskit.commands.combine_release_packages',
    'ocdskit.commands.compile',
    'ocdskit.commands.detect_format',
    'ocdskit.commands.echo',
    'ocdskit.commands.indent',
    'ocdskit.commands.mapping_sheet',
    'ocdskit.commands.package_records',
    'ocdskit.commands.package_releases',
    'ocdskit.commands.schema_report',
    'ocdskit.commands.schema_strict',
    'ocdskit.commands.set_closed_codelist_enums',
    'ocdskit.commands.split_record_packages',
    'ocdskit.commands.split_release_packages',
    'ocdskit.commands.upgrade',
)


# The arguments are for use in oc4idskit.
def main(description='Open Contracting Data Standard CLI', modules=COMMAND_MODULES, logger=logger):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--encoding', help='the file encoding')
    parser.add_argument('--ascii', help='print escape sequences instead of UTF-8 characters', action='store_true')
    parser.add_argument('--pretty', help='pretty print output', action='store_true')

    subparsers = parser.add_subparsers(dest='subcommand')

    subcommands = {}

    for module in modules:
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
                raise CommandError(f'JSON error: {e}') from e
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
    raise CommandError(f'encoding error: {e}\nTry `--encoding {suggestion}`?')


if __name__ == '__main__':
    main()
