import json
import sys
from copy import deepcopy
from functools import partial

from ocdskit.commands.base import BaseCommand
from ocdskit.hierarchy import get_base_classes_via_fca
from ocdskit.normalize import (
    convert_from_oas3,
    fix_validation_errors,
    get_normal_schema,
    hoist_deep_properties,
    normalize_schema,
    remove_fields,
    remove_private_fields,
    remove_unreachable_definitions,
)
from ocdskit.util import json_dump

try:
    import jsonschema_rs
except ImportError:
    jsonschema_rs = None
import jsonschema


class Command(BaseCommand):
    name = "normalize"
    help = "normalizes a denormalized JSON Schema"
    kwargs = {  # noqa: RUF012
        "epilog": (
            "The metadata and validation keywords after normalization are illustrative, "
            "not representative, of the original schema."
        )
    }

    def add_arguments(self):
        self.add_argument("file", help="the schema file")
        self.add_argument("--fix", action="store_true", help="fix validation errors")
        self.add_argument("--remove-private-fields", action="store_true", help="remove _* fields")
        self.add_argument("--remove-fields", nargs="+", help="remove specified fields")
        self.add_argument("--root-pattern", help="remove definitions unreachable from names matching this pattern")
        self.add_argument(
            "--ignore-x-keywords", action="store_true", help="when deduplicating classes, ignore x-* keywords"
        )
        self.add_argument(
            "--ignore-fields", nargs="+", default=[], help="when deduplicating classes, ignore specified fields"
        )
        self.add_argument(
            "--max-field-prevalence",
            type=float,
            default=1.0,
            help="when extracting base classes, ignore fields found in more than this proportion of classes",
        )
        self.add_argument(
            "--base-class-name-prefix", default="", help="prefix to disambiguate base classes from existing classes"
        )
        self.add_argument(
            "--get-only", action="store_true", help="if file is OpenAPI Schema, include only schemas used by GET paths"
        )
        self.add_argument(
            "--check", action="store_true", help="check the file for denormalization without modifying the file"
        )

    def handle(self):
        with open(self.args.file) as f:
            schema = json.load(f)

        normalizer = partial(
            get_normal_schema,
            remove_nontype_keywords=True,
            remove_x_keywords=self.args.ignore_x_keywords,
            remove_fields=set(self.args.ignore_fields),
        )

        # Get valid JSON Schema, and reduce its size.
        if schema.get("openapi", "").startswith("3.0"):
            schema = convert_from_oas3(schema, get_only=self.args.get_only)
        if self.args.remove_private_fields:
            remove_private_fields(schema)
        if self.args.remove_fields:
            remove_fields(schema, fields=set(self.args.remove_fields))
        if self.args.root_pattern:
            remove_unreachable_definitions(schema, self.args.root_pattern)
        if self.args.fix:
            fix_validation_errors(schema, normalizer=normalizer)

        if jsonschema_rs:
            jsonschema_rs.meta.validate(schema)
        else:
            jsonschema.validators.validator_for(schema).check_schema(schema)

        # Make all sets of `properties` into classes.
        hoist_deep_properties(schema, normalizer=normalizer)

        # Copy input for `check` mode.
        original = deepcopy(schema)

        # Normalize the schema.
        get_base_classes = partial(
            get_base_classes_via_fca,
            max_field_prevalence=self.args.max_field_prevalence,
            base_class_name_prefix=self.args.base_class_name_prefix,
        )
        normalize_schema(schema, normalizer, get_base_classes)

        if self.args.check:
            if schema != original:
                print(f"ERROR: {self.args.file} is denormalized", file=sys.stderr)
        else:
            with open(self.args.file, "w") as f:
                json_dump(schema, f, indent=2)
                f.write("\n")
