import os.path
import pathlib
import sys

import jsonref
from ocdsextensionregistry import ProfileBuilder

from .base import BaseCommand
from ocdskit.exceptions import CommandError, MissingColumnError
from ocdskit.mapping_sheet import mapping_sheet
from ocdskit.util import json_load


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths in a JSON Schema'

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--order-by', help="sort the spreadsheet's rows by this column")
        self.add_argument('--infer-required', action='store_true', help='infer whether fields are required')
        self.add_argument('--extension', nargs='*', help='patch the release schema with this extension')
        self.add_argument('--extension-field', help='add an "extension" column with values from this schema field')

    def handle(self):
        with open(self.args.file) as f:
            schema = json_load(f)

        if self.args.extension:
            builder = ProfileBuilder(None, self.args.extension)
            schema = builder.patched_release_schema(schema=schema, extension_field=self.args.extension_field)

        base_uri = pathlib.Path(os.path.realpath(self.args.file)).as_uri()
        schema = jsonref.JsonRef.replace_refs(schema, base_uri=base_uri)

        try:
            mapping_sheet(schema, sys.stdout, order_by=self.args.order_by, infer_required=self.args.infer_required,
                          extension_field=self.args.extension_field)
        except MissingColumnError as e:
            raise CommandError(str(e))
