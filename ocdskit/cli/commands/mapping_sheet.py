import sys

from .base import BaseCommand
from ocdskit.exceptions import CommandError, MissingColumnError
from ocdskit.mapping_sheet import mapping_sheet


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths from an OCDS or BODS schema'

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--order-by', help="sort the spreadsheet's rows by this column")

    def handle(self):
        try:
            mapping_sheet(self.args.file, sys.stdout, self.args.order_by)
        except MissingColumnError as e:
            raise CommandError(str(e))
