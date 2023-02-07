import csv
import json
import pathlib
import sys
from argparse import RawDescriptionHelpFormatter
from textwrap import dedent

from ocdsextensionregistry import ProfileBuilder

from ocdskit.commands.base import BaseCommand
from ocdskit.exceptions import CommandError, MissingColumnError
from ocdskit.mapping_sheet import mapping_sheet


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths in a JSON Schema'
    kwargs = {
        'epilog': dedent(
            """
            The --extension option must be declared after the file argument. It accepts multiple values, which can be
            extensions' metadata URLs, base URLs and/or download URLs. For example:

                ocdskit mapping-sheet release-schema.json --extension \\
                    https://raw.githubusercontent.com/open-contracting-extensions/ocds_coveredBy_extension/master/extension.json \\
                    https://raw.githubusercontent.com/open-contracting-extensions/ocds_options_extension/master/ \\
                    https://github.com/open-contracting-extensions/ocds_techniques_extension/archive/master.zip \\
                    > mapping-sheet.csv

            The --extension-field option can be used with or without the --extension option.

            - If the --extension option is set, then the --extension-field option may be set to any value. In all
              cases, the result is a mapping sheet with an "extension" column, containing the name of the extension in
              which each field was defined.

            - If the --extension option is not set, then the --extension-field option must be set to the property in
              the JSON schema containing the name of the extension in which each field was defined. If there is no such
              property, then the result is a mapping sheet with no values in its "extension" column.
            """  # noqa: E501
        ),
        'formatter_class': RawDescriptionHelpFormatter,
    }

    def add_arguments(self):
        self.add_argument('file', help='the schema file')
        self.add_argument('--order-by', help="sort the spreadsheet's rows by this column")
        self.add_argument('--infer-required', action='store_true', help='infer whether fields are required')
        self.add_argument('--extension', nargs='*', help='patch the release schema with this extension')
        self.add_argument('--extension-field', help='add an "extension" column for the name of the extension in which '
                          'each field was defined')
        self.add_argument('--no-inherit-extension', action='store_true', help='fields defined via $ref properties do '
                          'not inherit the "extension" value of their parent field')
        self.add_argument('--language', default='en', help='the language to use for the name of the extension')
        self.add_argument('--codelist', action='store_true', help='add a "codelist" column')
        self.add_argument('--no-deprecated', action='store_true', help="don't include deprecated fields")
        self.add_argument('--no-replace-refs', action='store_true', help="don't replace schema with $ref properties "
                          'with the referenced schema')

    def handle(self):
        with open(self.args.file) as f:
            schema = json.load(f)

        if self.args.extension:
            builder = ProfileBuilder(None, self.args.extension)
            schema = builder.patched_release_schema(
                schema=schema, extension_field=self.args.extension_field, language=self.args.language
            )

        try:
            fieldnames, rows = mapping_sheet(
                schema,
                order_by=self.args.order_by,
                infer_required=self.args.infer_required,
                extension_field=self.args.extension_field,
                inherit_extension=not self.args.no_inherit_extension,
                include_codelist=self.args.codelist,
                include_deprecated=not self.args.no_deprecated,
                include_definitions=self.args.no_replace_refs,
                base_uri=pathlib.Path(self.args.file).resolve().as_uri(),
            )

            writer = csv.DictWriter(sys.stdout, fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        except MissingColumnError as e:
            raise CommandError(str(e)) from e
