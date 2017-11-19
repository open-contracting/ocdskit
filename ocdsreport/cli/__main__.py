import argparse
import importlib
import logging.config
import sys

from ocdskit.exceptions import CommandError

logger = logging.getLogger('pupa')

COMMAND_MODULES = (
    'ocdskit.cli.commands.compile',
    'ocdskit.cli.commands.measure',
    'ocdskit.cli.commands.validate',
)


def main():
    parser = argparse.ArgumentParser(description='reporting CLI')
    parser.add_argument('--encoding', help='the file encoding')

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
            data = command.read(args.encoding)
            command.handle(args, data)
        except CommandError as e:
            logger.critical(e)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
