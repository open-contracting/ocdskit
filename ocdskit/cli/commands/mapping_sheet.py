import sys

from .base import BaseCommand
from ocdskit.mapping_sheet import mapping_sheet


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths from an OCDS schema'

    def handle(self):
        mapping_sheet(self.buffer(), sys.stdout)
