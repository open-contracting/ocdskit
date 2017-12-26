import argparse
import importlib
import logging.config
import sys

from ocdskit.exceptions import CommandError

logger = logging.getLogger('ocdskit')

COMMAND_MODULES = (
    'ocdskit.cli.commands.combine_record_packages',
    'ocdskit.cli.commands.combine_release_packages',
    'ocdskit.cli.commands.compile',
    'ocdskit.cli.commands.mapping_sheet',
    'ocdskit.cli.commands.measure',
    'ocdskit.cli.commands.tabulate',
    'ocdskit.cli.commands.validate',
)


def main():
    parser = argparse.ArgumentParser(description='Open Contracting Data Standard CLI')
    parser.add_argument('--encoding', help='the file encoding')
    parser.add_argument('--pretty', action='store_true', help='pretty print output')

    subparsers = parser.add_subparsers(dest='subcommand')

    subcommands = {}

    for module in COMMAND_MODULES:
        try:
            command = importlib.import_module(module).Command(subparsers)
            subcommands[command.name] = command
        except ImportError as e:
            logger.error('exception "%s" prevented loading of %s module', e, module)

    args = parser.parse_args()

    if args.subcommand:
        command = subcommands[args.subcommand]
        try:
            command.args = args
            try:
                command.handle()
            except UnicodeDecodeError as e:
                if args.encoding and args.encoding.lower() == 'iso-8859-1':
                    suggestion = 'utf-8'
                else:
                    suggestion = 'iso-8859-1'
                raise CommandError('encoding error: try `--encoding {}`? ({})'.format(suggestion, e))
        except CommandError as e:
            logger.critical(e)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
