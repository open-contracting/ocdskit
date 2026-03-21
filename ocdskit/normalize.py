import functools
import json
import zlib
from collections import defaultdict

from ocdskit.util import _get_prop_name, _split_camel_case, longest_common_subsequence

VALIDATION_AND_METADATA_KEYWORDS = {  # except `type`
    # https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-00#rfc.section.6
    # Any
    "enum",
    "const",
    # Numeric
    "multipleOf",
    "maximum",
    "exclusiveMaximum",
    "minimum",
    "exclusiveMinimum",
    # String
    "maxLength",
    "minLength",
    "pattern",
    # Array
    "maxItems",
    "minItems",
    "uniqueItems",
    "maxContains",
    "minContains",
    # Object
    "minProperties",
    "maxProperties",
    "required",
    "dependentRequired",
    # https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-00#rfc.section.7
    "format",
    # https://json-schema.org/draft/2020-12/draft-bhutton-json-schema-validation-00#rfc.section.9
    "title",
    "description",
    "default",
    "deprecated",
    "readOnly",
    "writeOnly",
    "examples",
    # https://swagger.io/specification/v3/#fixed-fields-21
    "nullable",
    "discriminator",
    "xml",
    "externalDocs",
    "example",
}
# https://json-schema.org/draft/2020-12/meta/applicator
APPLICATOR_KEYWORDS = {
    "prefixItems",
    "additionalItems",  # removed in draft 2020-12
    "items",
    "contains",
    "additionalProperties",
    "properties",
    "patternProperties",
    "dependentSchemas",
    "propertyNames",
    "if",
    "then",
    "else",
    "allOf",
    "anyOf",
    "oneOf",
    "not",
}


def _traverse_in_place(block):
    def _method(value):
        if isinstance(value, dict):
            block(value)
            for v in value.values():
                _method(v)
        elif isinstance(value, list):
            for v in value:
                _method(v)

    return _method


def get_definitions_keyword(schema):
    """
    Return the schema's definitions keyword, defaulting to ``$defs``.

    :param dict schema: a JSON schema
    :returns: ``"$defs"`` or ``"definitions"``
    :rtype: str
    """
    return next((keyword for keyword in ("$defs", "definitions") if keyword in schema), "$defs")


def get_schema_hash(schema, normalizer):
    """
    :param dict schema: a JSON schema
    :param normalizer: a function that accepts a JSON Schema and returns a JSON Schema,
        with all structurally-irrelevant properties removed
    :returns: a checksum
    :rtype: int
    """
    return zlib.crc32(json.dumps(normalizer(schema), sort_keys=True).encode())


def get_base_class_name(class_names, prefix="Base"):
    """Derive a base class name from the longest common subsequence of words within class names."""
    if len(class_names) < 2:
        return None

    sequences = [_split_camel_case(name) for name in class_names]

    lcs = sequences[0]
    for sequence in sequences[1:]:
        lcs = longest_common_subsequence(lcs, sequence)
        if not lcs:
            return None

    seen = set()
    unique = []
    for word in lcs:
        if word not in seen:
            seen.add(word)
            unique.append(word)

    return prefix + "".join(unique)


def convert_from_oas3(schema, *, get_only=False):
    """
    Convert from OpenAPI Specification 3.0 to JSON Schema draft 4.

    .. warning::

       Modifies schema ``$ref`` values in-place.

    .. admonition:: Limitations

       Unsupported:

       -  Schema Objects not under ``#/components/schemas``
       -  External ``$ref`` to Schema Objects
       -  Any ``$ref`` to Response Objects
       -  Any ``$ref`` to Path Item Objects

    :param dict value: a JSON schema
    :param bool get_only: whether to convert only schemas used by GET paths
    :returns: a schema using JSON Schema draft 4
    :rtype: object
    """

    def _replace_refs(value):
        if (ref := value.get("$ref")) and ref.startswith("#/components/schemas/"):
            name = ref[21:]
            # Update the reference.
            value["$ref"] = f"#/definitions/{name}"
            if name not in definitions:
                definition = schemas[name]
                # Add to the schema's definitions.
                definitions[name] = definition
                # Recurse into the referenced definition.
                replace_refs(definition)

    replace_refs = _traverse_in_place(_replace_refs)

    # https://swagger.io/specification/v3/#openapi-object
    schemas = schema.get("components", {}).get("schemas", {})

    if not get_only:
        definitions = schemas
        replace_refs(schemas)
    else:
        definitions = {}
        for path_item_object in schema["paths"].values():
            if operation := path_item_object.get("get"):
                # `responses` is required, but the schema can be invalid.
                for response in operation.get("responses", {}).values():
                    for media_type in response.get("content", {}).values():
                        if schema_object := media_type.get("schema"):
                            replace_refs(schema_object)

    return {"$schema": "http://json-schema.org/draft-04/schema#", "definitions": definitions}


def _remove_private_fields(value):
    if properties := value.get("properties"):
        value["properties"] = {name: subschema for name, subschema in properties.items() if not name.startswith("_")}


remove_private_fields = _traverse_in_place(_remove_private_fields)
"""
Remove ``properties`` members that start with underscores.

.. warning::

   Assumes ``properties`` is never a direct member of the ``properties`` validation keyword.

:param dict value: a JSON schema
"""


def remove_fields(schema, fields):
    """
    Remove the given fields from the ``properties`` mapping.

    .. warning::

       Assumes ``properties`` is never a direct member of the ``properties`` validation keyword.

    :param dict value: a JSON schema
    :param set[str] fields: fields to remove
    """

    def _remove_fields(value):
        if properties := value.get("properties"):
            value["properties"] = {name: subschema for name, subschema in properties.items() if name not in fields}

    _traverse_in_place(_remove_fields)(schema)


def remove_unreachable_definitions(schema, pattern):
    """
    Remove any definitions that are unreachable from definitions whose names contain ``pattern``.

    Performs a breadth-first search from the root definitions, following ``$ref`` edges.

    :param dict schema: a JSON schema
    :param str pattern: a substring to case-sensitively match against definition names
    """

    def _build_graph(value, source):
        if isinstance(value, dict):
            if (ref := value.get("$ref")) and ref.startswith(ref_prefix):
                target = ref[len_prefix:]
                if target in definitions:
                    graph[source].add(target)
            for v in value.values():
                _build_graph(v, source)
        elif isinstance(value, list):
            for v in value:
                _build_graph(v, source)

    definitions_keyword = get_definitions_keyword(schema)
    definitions = schema.get(definitions_keyword, {})

    graph = defaultdict(set)
    ref_prefix = f"#/{definitions_keyword}/"
    len_prefix = len(ref_prefix)
    for name, definition in definitions.items():
        _build_graph(definition, name)

    # Breadth-first search.
    keep = set()
    queue = [name for name in definitions if pattern in name]
    while queue:
        node = queue.pop()
        if node not in keep:
            keep.add(node)
            queue.extend(target for target in graph[node] if target not in keep)

    for name in list(definitions):
        if name not in keep:
            del definitions[name]


def fix_validation_errors(schema, normalizer=None):
    """
    Fix validation errors in a JSON Schema.

    Changes ``anyOf`` from an object to an array, deduplicating values based on their normalized form.

    .. warning::

       Assumes ``anyOf`` is never a direct member of the ``properties`` validation keyword.

    :param dict schema: a JSON schema
    :param normalizer:  a function that accepts a JSON Schema and returns a JSON Schema,
        with all structurally-irrelevant properties removed, for deduplication
    """

    def _fix_validation_errors(value):
        if (anyof := value.get("anyOf")) and isinstance(anyof, dict):
            seen = []
            value["anyOf"] = []
            for v in anyof.values():
                normalized = normalizer(v) if normalizer else v
                if normalized not in seen:
                    seen.append(normalized)
                    value["anyOf"].append(v)

    _traverse_in_place(_fix_validation_errors)(schema)


def get_normal_schema(value, *, remove_nontype_keywords=False, remove_x_keywords=False, remove_fields=()):
    """
    Remove metadata and validation keywords, ``x-*`` keywords and/or specific fields.

    .. warning::

       Assumes ``properties`` is never a direct member of the ``properties`` validation keyword.

    :param dict value: a JSON schema
    :param bool remove_nontype_keywords: whether to remove metadata and validation keywords
    :param bool remove_x_keywords: whether to remove ``x-*`` keywords
    :param set[str] remove_fields: fields to remove
    :returns: a new schema with keywords removed
    :rtype: object
    """
    recurse = functools.partial(
        get_normal_schema,
        remove_nontype_keywords=remove_nontype_keywords,
        remove_x_keywords=remove_x_keywords,
        remove_fields=remove_fields,
    )

    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if remove_nontype_keywords and k in VALIDATION_AND_METADATA_KEYWORDS:
                continue
            if remove_x_keywords and k.startswith("x-"):
                continue
            if k == "properties":  # avoid removing properties with the same names as keywords
                result[k] = {pk: recurse(pv) for pk, pv in v.items() if not (remove_fields and pk in remove_fields)}
            else:
                result[k] = recurse(v)
        return result
    if isinstance(value, list):
        return [recurse(v) for v in value]
    return value


def hoist_deep_properties(schema, normalizer):
    """
    Move any sub-schema with a ``properties`` keyword to the definitions location.

    If neither ``$defs`` nor ``definitions`` exists, ``$defs`` is used.

    The schema is named using its ``title`` keyword, or its parent property.

    .. warning::

       Assumes ``properties`` is never a direct member of the ``properties`` validation keyword.

    .. admonition:: Limitations

       The schema is named after an earlier ancestor if the parent property has the same name as an
       `applicator keyword <https://json-schema.org/draft/2020-12/meta/applicator>`__.

    :param dict schema: a JSON schema
    :param normalizer: a function that accepts a JSON Schema and returns a JSON Schema,
        with all structurally-irrelevant properties removed
    """

    def _hoist(value, key, parent, definition=None, definition_name=None, prop=""):
        if isinstance(value, dict):
            if "properties" in value and value is not definition:  # don't hoist at top level
                hashed = hasher(value)
                name = hashes.get(hashed)
                # Hoist if no match.
                if not name:
                    name = value.get("title")
                    if not name:  # don't use default argument to `get` in case prop is empty
                        name = prop[0].upper() + prop[1:]
                    if name in definitions:
                        name = f"{name}_{format(hashed & 0xFFFFFFFF, '08x')}"
                    definitions[name] = value
                    hashes[hashed] = name
                # Replace the properties with a $ref.
                parent[key] = {"$ref": f"#/{definition_keyword}/{name}"}
                # Recalculate the current definition's hash.
                if definition is not None:
                    hashes[hasher(definition)] = definition_name
            # Special case for allOf inheritance.
            if value is definition and "allOf" in value and len(value) == 1:
                for i, v in enumerate(definition["allOf"]):
                    _hoist(v, i, value["allOf"], v, definition_name, prop)
            else:
                for k, v in value.items():
                    _hoist(v, k, value, definition, definition_name, prop if k in APPLICATOR_KEYWORDS else k)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                _hoist(v, i, value, definition, definition_name, prop)

    hasher = functools.partial(get_schema_hash, normalizer=normalizer)
    definition_keyword = get_definitions_keyword(schema)
    definitions = schema.setdefault(definition_keyword, {})
    hashes = {hasher(definition): definition_name for definition_name, definition in definitions.items()}

    for definition_name, definition in list(definitions.items()):
        _hoist(definition, definition_name, definitions, definition, definition_name)

    schema.pop(definition_keyword)  # avoid re-processing definitions
    for key, value in schema.items():
        _hoist(value, key, schema)
    schema[definition_keyword] = definitions


def normalize_schema(schema, normalizer, get_base_classes):
    """
    Extract base classes from a schema's definitions. Rewrite definitions to use ``allOf`` inheritance.

    Hashes each ``properties`` member using ``normalizer``, calls ``get_base_classes``, then performs greedy set-cover
    to determine multiple inheritance for both base classes and original definitions.

    All ``properties`` mappings must be at definitions' top-level. See :ref:`~ocdskit.normalize.hoist_deep_properties`.

    .. warning::

       Modifies ``schema`` in-place.

    :param dict schema: a JSON schema
    :param normalizer: a function that accepts a JSON Schema and returns a JSON Schema,
        with all structurally-irrelevant properties removed
    :param get_base_classes: a function that accepts the schema's definitions as a mapping of definition names to sets
         of ``{prop}:{hash}`` strings, and returns base classes as a list of dicts with the keys:

         ``name``
           The name of the base class
         ``members``
           A sequence of child classes
         ``props``
           A set of ``{prop}:{hash}`` strings
    """
    definitions_keyword = get_definitions_keyword(schema)
    definitions = schema[definitions_keyword]
    ref_prefix = f"#/{definitions_keyword}/"

    # Base class calculation requires hashable values.
    classes = defaultdict(set)
    hashed_to_schema = {}
    for name, definition in definitions.items():
        if "properties" in definition:
            for prop, subschema in definition["properties"].items():
                hashed = f"{prop}:{get_schema_hash(subschema, normalizer)}"
                classes[name].add(hashed)
                hashed_to_schema[hashed] = subschema

    # Calculate base classes.
    base_classes = get_base_classes(classes)

    # Invert base classes.
    subclass_bases = defaultdict(list)
    for base_class in base_classes:
        for subclass in base_class["members"]:
            subclass_bases[subclass].append(base_class)

    # Greedy set-cover: for each class, find the fewest bases that cover its properties.
    used_bases = set()
    specificity_order = sorted(base_classes, key=lambda base_class: -len(base_class["props"]))

    # Inheritance between base classes.
    base_allofs = {}
    for i, base_class in enumerate(specificity_order):
        allof = []
        covered = set()
        for other in specificity_order[i + 1 :]:
            if other["props"] < base_class["props"] and other["props"] - covered:
                allof.append(other)
                covered |= other["props"]
        if allof:
            base_allofs[base_class["name"]] = allof
            used_bases.update(id(base) for base in allof)

    # Inheritance between original classes and base classes.
    subclass_allofs = {}
    for subclass, bases in subclass_bases.items():
        allof = []
        covered = set()
        for base_class in sorted(bases, key=lambda base_class: -len(base_class["props"])):
            if base_class["props"] - covered:
                allof.append(base_class)
                covered |= base_class["props"]
        subclass_allofs[subclass] = allof
        used_bases.update(id(base) for base in allof)

    # Add base classes to schema definitions.
    for base_class in base_classes:
        if id(base_class) not in used_bases:
            continue
        name = base_class["name"]
        if allof := base_allofs.get(name):
            subschema = {"allOf": [{"$ref": f"{ref_prefix}{base['name']}"} for base in allof]}
            if remaining := base_class["props"] - set().union(*(base["props"] for base in allof)):
                properties = {_get_prop_name(p): hashed_to_schema[p] for p in remaining}
                subschema["allOf"].append({"type": "object", "properties": properties})
        else:
            properties = {_get_prop_name(p): hashed_to_schema[p] for p in base_class["props"]}
            subschema = {"type": "object", "properties": properties}
        definitions[name] = subschema

    # Modify existing definitions to reference base classes.
    for subclass, allof in subclass_allofs.items():
        definition = definitions[subclass]
        properties = definition["properties"]

        # Remove properties covered by base classes.
        for base in allof:
            for prop in base["props"]:
                if prop in classes[subclass]:
                    properties.pop(_get_prop_name(prop), None)  # a property can be covered by multiple base classes
        if not properties:
            del definition["properties"]

        # Build allOf value.
        value = [{"$ref": f"{ref_prefix}{base['name']}"} for base in allof]
        value.append(definition.copy())
        definition.clear()
        definition["allOf"] = value
