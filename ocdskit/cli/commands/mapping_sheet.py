import os.path
import pathlib
import sys
from collections import OrderedDict

import jsonref

from .base import BaseCommand
from ocdskit.exceptions import CommandError, MissingColumnError
from ocdskit.mapping_sheet import mapping_sheet


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths from an OCDS, OC4IDS or BODS schema'

    def add_arguments(self):
        self.add_argument('file',
                          help='the schema file')
        self.add_argument('--order-by',
                          help="sort the spreadsheet's rows by this column")
        self.add_argument('--infer-required', action='store_true',
                          help='infer whether fields are required')
        self.add_argument('--extension-field',
                          help='add an "extension" column with values from this schema field')

    def handle(self):
        with open(self.args.file) as f:
            schema = jsonref.load(f, object_pairs_hook=OrderedDict,
                                  base_uri=pathlib.Path(os.path.realpath(self.args.file)).as_uri())

        try:
            mapping_sheet(schema, sys.stdout, order_by=self.args.order_by, infer_required=self.args.infer_required,
                          extension_field=self.args.extension_field)
        except MissingColumnError as e:
            raise CommandError(str(e))
