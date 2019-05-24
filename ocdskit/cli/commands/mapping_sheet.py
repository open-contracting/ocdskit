import sys

from .base import BaseCommand
from ocdskit.exceptions import CommandError, MissingColumnError
from ocdskit.mapping_sheet import MappingSheet


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths from an OCDS, OC4IDS or BODS schema'

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--order-by', help="sort the spreadsheet's rows by this column")
        self.add_argument('--infer-required', help='infer whether fields are required', action='store_true')

    def handle(self):
        try:
            MappingSheet().run(self.args.file, sys.stdout, self.args.order_by, self.args.infer_required)
        except MissingColumnError as e:
            raise CommandError(str(e))
