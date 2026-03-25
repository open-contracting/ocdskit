import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from ocdskit.commands.base import BaseCommand
from ocdskit.dot import get_erd
from ocdskit.util import get_definitions_keyword


def _get_refs(value):
    """Yield all schema names from $ref values in a JSON Schema."""
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"].rpartition("/")[2]
        for v in value.values():
            yield from _get_refs(v)
    elif isinstance(value, list):
        for v in value:
            yield from _get_refs(v)


def _auto_threshold(ref_counts, min_relative_gap=0.2):
    """
    Return a threshold based on the largest relative gap in sorted reference counts.

    Returns None if the largest gap is relatively small.
    """
    # NOTE: The kneed package might improve threshold selection for some inputs.
    if len(ref_counts) < 2:
        return None
    counts = sorted(ref_counts.values(), reverse=True)
    max_gap, index = max(((counts[i] - counts[i + 1]) / counts[i], i) for i in range(len(counts) - 1))
    if max_gap < min_relative_gap:
        return None
    return counts[index]


class Command(BaseCommand):
    name = "erd"
    help = "generates an entity-relationship diagram from a normalized JSON Schema"

    def add_arguments(self):
        self.add_argument("file", help="the schema file")
        self.add_argument("output", help="the output file")
        self.add_argument("--no-properties", action="store_true", help="show schema names and relationships only")
        self.add_argument(
            "--max-properties", type=int, metavar="N", help="truncate schema properties (default: unlimited)"
        )
        self.add_argument(
            "--threshold", type=int, help="add schemas referenced this many times to a subgraph (default: auto)"
        )
        self.add_argument(
            "--root-pattern", metavar="PATTERN", help="never add schemas matching this regex to the subgraph"
        )
        self.add_argument(
            "--cluster",
            action="append",
            default=[],
            metavar="PATTERN",
            help="force schema names matching this regex into one color cluster (repeatable, evaluated in order)",
        )
        self.add_argument(
            "--ignore-words",
            nargs="+",
            default=[],
            metavar="WORD",
            help="when color clustering, ignore these words in schema names",
        )
        self.add_argument(
            "--ignore-before",
            metavar="SEP",
            help="when color clustering, ignore the parts of schema names before this character",
        )
        self.add_argument(
            "--base-class-name-prefix", default="", help="prefix to disambiguate base classes from existing classes"
        )
        self.add_argument("-v", "--verbose", action="store_true", help="print verbose output to stderr")

    def handle(self):
        with open(self.args.file) as f:
            schema = json.load(f)

        definitions_keyword = get_definitions_keyword(schema)
        definitions = schema.pop(definitions_keyword, {})
        if "properties" in schema:
            definitions["erd.Root"] = schema

        # Build forward and reverse reference maps and total reference counts.
        references = defaultdict(set)
        referrers = defaultdict(set)
        ref_counts = defaultdict(int)

        for name, definition in definitions.items():
            for ref in _get_refs(definition):
                references[name].add(ref)
                referrers[ref].add(name)
                ref_counts[ref] += 1

        # Calculate basic schemas to add to the subgraph.
        basic_names = set()
        if threshold := self.args.threshold if self.args.threshold is not None else _auto_threshold(ref_counts):
            basic_names = {name for name, count in ref_counts.items() if count >= threshold}

            class_names = set(definitions)
            changed = True
            while changed:
                changed = False
                for name in class_names - basic_names:
                    # Treat as basic any non-root schema referenced only by basic schemas.
                    if set() < referrers[name] <= basic_names:
                        basic_names.add(name)
                        changed = True

            if self.args.root_pattern:
                root_pattern = re.compile(self.args.root_pattern)
                basic_names -= {name for name in basic_names if root_pattern.search(name)}

            if basic_names:
                print(f"Omitting {len(basic_names)} basic schemas referenced >= {threshold} times:", file=sys.stderr)
                for name in sorted(basic_names):
                    print(f"  {name} ({ref_counts[name]} refs)", file=sys.stderr)

        result = get_erd(
            definitions,
            no_properties=self.args.no_properties,
            max_properties=self.args.max_properties,
            subgraph=basic_names,
            manual_clusters=self.args.cluster,
            ignore_words=self.args.ignore_words,
            ignore_before=self.args.ignore_before,
            base_class_name_prefix=self.args.base_class_name_prefix,
            verbose=self.args.verbose,
        )

        Path(self.args.output).write_text(result)
