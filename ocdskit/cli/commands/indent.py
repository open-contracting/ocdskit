import json
import logging
import os.path

from ocdskit.cli.commands.base import BaseCommand
from ocdskit.util import json_dump

logger = logging.getLogger('ocdskit')


class Command(BaseCommand):
    name = 'indent'
    help = 'indents JSON files by modifying the given files in-place'

    def add_arguments(self):
        self.add_argument('file', help='files to reindent', nargs='+')
        self.add_argument('-r', '--recursive', help='recursively indent JSON files', action='store_true')
        self.add_argument('--indent', help='indent level', type=int, default=2)

    def handle(self):
        for file in self.args.file:
            if os.path.isfile(file):
                self.indent(file)
            elif self.args.recursive:
                for root, dirs, files in os.walk(file):
                    for name in files:
                        if name.endswith('.json'):
                            self.indent(os.path.join(root, name))
            elif os.path.isdir(file):
                logger.warning('{} is a directory. Set --recursive to recurse into directories.'.format(file))
            else:
                logger.error('{}: No such file or directory'.format(file))

    def indent(self, path):
        try:
            with open(path) as f:
                data = json.load(f)

            with open(path, 'w') as f:
                json_dump(data, f, indent=self.args.indent, ensure_ascii=self.args.ascii)
                f.write('\n')
        except json.decoder.JSONDecodeError as e:
            logger.error('{} is not valid JSON. (json.decoder.JSONDecodeError: {})'.format(path, e))
