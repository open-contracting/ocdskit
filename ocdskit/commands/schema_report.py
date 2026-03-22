import csv
import json
import pathlib
import sys
from collections import defaultdict
from operator import itemgetter

import jsonref

from ocdskit.commands.base import BaseCommand
from ocdskit.schema import get_schema_fields

KEYWORDS_TO_IGNORE = (
    # Metadata keywords
    # https://tools.ietf.org/html/draft-fge-json-schema-validation-00#section-6
    "title",
    "description",
    "default",
    # Extended keywords
    # http://os4d.opendataservices.coop/development/schema/#extended-json-schema
    "omitWhenMerged",
    "wholeListMerge",
    "versionId",
)


class Command(BaseCommand):
    name = "schema-report"
    help = "reports details of a JSON Schema"

    def add_arguments(self):
        self.add_argument("file", help="the schema file")
        self.add_argument("--field-count", action="store_true", help="report the number of fields")
        self.add_argument("--codelists", action="store_true", help="report open and closed codelists")
        self.add_argument(
            "--definitions",
            action="store_true",
            help="report definitions that can use a common $ref in the versioned release schema",
        )
        self.add_argument(
            "--min-occurrences",
            type=int,
            default=5,
            help="report definitions that occur at least this many times (default 5)",
        )

    def handle(self):
        def _add_definition(data):
            if "$ref" not in data:
                definition = {key: value for key, value in sorted(data.items()) if key not in KEYWORDS_TO_IGNORE}
                definitions[repr(definition)] += 1

        def _recurse(data):
            if isinstance(data, list):
                for item in data:
                    _recurse(item)
            elif isinstance(data, dict):
                if "codelist" in data:
                    open_codelist = data.get("openCodelist", "enum" not in data)
                    codelists[data["codelist"]].add(open_codelist)

                for key, value in data.items():
                    # Find definitions that can use a common $ref in the versioned release schema. Unversioned fields,
                    # like the `id`'s of objects in arrays that are not `wholeListMerge`, should be excluded, but it's
                    # too much work with too little advantage to do so.
                    if key in {"$defs", "definitions", "properties"}:
                        for definition in value.values():
                            _add_definition(definition)
                    _recurse(value)

        with open(self.args.file) as f:
            text = f.read()

        if self.args.codelists or self.args.definitions:
            deref_schema = jsonref.loads(text, base_uri=pathlib.Path(self.args.file).resolve().as_uri())

            codelists = defaultdict(set)
            definitions = defaultdict(int)
            _recurse(deref_schema)

            if self.args.codelists:
                writer = csv.writer(sys.stdout, lineterminator="\n")
                writer.writerow(["codelist", "openCodelist"])
                for codelist, openness in sorted(codelists.items()):
                    writer.writerow([codelist, "/".join(str(value) for value in sorted(openness))])

            if self.args.codelists and self.args.definitions:
                print()

            if self.args.definitions:
                for definition, count in sorted(definitions.items(), key=itemgetter(1), reverse=True):
                    if count < self.args.min_occurrences:
                        break
                    print(f"{count:2d}: {definition}")

        if self.args.field_count:
            schema = json.loads(text)
            print(f"{sum(1 for field in get_schema_fields(schema))} fields")
