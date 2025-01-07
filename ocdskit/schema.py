from __future__ import annotations

from dataclasses import dataclass

LANGUAGE_CODE_SUFFIX = '_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+))'  # noqa: E501
LANGUAGE_CODE_SUFFIX_LEN = len(LANGUAGE_CODE_SUFFIX)


@dataclass
class Field:
    """Initialize a schema field object."""

    #: The field's name.
    name: str
    #: The field's schema.
    schema: dict
    #: The ``deprecated`` property of the field.
    deprecated_self: dict
    #: The ``deprecated`` property of the field, or an ancestor of the field.
    deprecated: dict
    #: The JSON pointer to the field in the schema, e.g. ``/properties/tender/properties/id``.
    #: Used, for example, to look up a modified field's original schema in the release schema.
    pointer: str
    #: The path to the field in data, e.g. ``('tender', 'id')``.
    path_components: tuple
    #: The definition in which the field is defined, e.g. ``'Item'``.
    definition: str
    #: Whether the field is defined under ``patternProperties``.
    pattern: bool = False
    #: Whether the field has a corresponding field in the schema's ``patternProperties`` (like in OCDS 1.1).
    multilingual: bool = False
    #: Whether the field is listed under ``required``.
    required: bool = False
    #: Whether the field's name is ``id`` and isn't under a ``wholeListMerge`` array.
    merge_by_id: bool = False
    #: The field's codelist.
    codelist: str = ''
    #: Whether the field's codelist is open.
    open_codelist: bool = False
    #: The separator to use in string representations of paths.
    sep = '.'

    @property
    def path(self):
        """Return the path to the field in data with ``self.sep`` as separator, e.g. ``tender.id``."""
        return self.sep.join(self.path_components)

    def __repr__(self):
        return repr(self.asdict())

    def asdict(self, sep=None, exclude=()):
        """
        Return the field as a dict, with keys for all properties except ``path_components``.

        :param list sep: the separator to use in string representations of paths, overriding ``self.sep``
        :param list exclude: a list of keys to exclude from the dict
        """
        sep = sep or self.sep

        return (
            {k: v for k, v in self.__dict__.items() if k not in exclude and k != 'path_components'}
            | ({} if 'path' in exclude else {'path': sep.join(self.path_components)})
        )


def get_schema_fields(
    schema: dict,
    pointer: str = '',
    path_components: tuple = (),
    definition: str = '',
    deprecated: dict | None = None,
    *,
    whole_list_merge: bool = False,
    array: bool = False,
):
    """
    Yield a :class:`~ocdskit.schema.Field` for each name under ``properties`` or ``patternProperties``.

    :param schema: A dereferenced JSON schema. If using ``jsonref``, and if subschemas set both ``$ref`` and other
        properties, the schema must be dereferenced with either ``proxies=True`` or ``merge_props=True``.
    :param pointer: The JSON pointer to the field in the schema, e.g. ``/properties/tender/properties/id``.
    :param path_components: The path to the field in data, e.g. ``('tender', 'id')``.
    :param definition: The definition in which the field is defined, e.g. ``'Item'``.
    :param deprecated: If the field, or an ancestor of the field, sets ``deprecated``, the ``deprecated`` object.
    :param whole_list_merge: Whether the field, or an ancestor of the field, sets ``wholelistMerge``.
    :param array: Whether the field is under ``items/properties`` or  ``items/patternProperties``.
    """
    multilingual = set()
    nonmultilingual_pattern_properties = {}

    required = schema.get('required', [])
    # `deprecated` and `whole_list_merge` are inherited.
    deprecated = deprecated or _deprecated(schema)
    whole_list_merge = whole_list_merge or schema.get('wholeListMerge', False)

    if pattern_properties := schema.get('patternProperties'):
        for pattern, subschema in pattern_properties.items():
            # The pattern might have an extra set of parentheses (like in OCDS 1.1). Assumes the final character is $.
            for offset in (2, 1):
                end = -LANGUAGE_CODE_SUFFIX_LEN - offset
                # The pattern must be anchored and the suffix must occur at the end.
                if (
                    pattern[end:-offset] == LANGUAGE_CODE_SUFFIX
                    and pattern[:offset] == '^('[:offset]
                    and pattern[-offset:] == ')$'[-offset:]
                ):
                    multilingual.add(pattern[offset:end])
                    break
            # Set `multilingual` on corresponding `properties`. Yield remaining `patternProperties`.
            else:
                nonmultilingual_pattern_properties[pattern] = subschema

    if items := schema.get('items'):
        # `items` advances the pointer and sets array context (for the next level only).
        if isinstance(items, dict):
            yield from get_schema_fields(
                items,
                f'{pointer}/items',
                path_components,
                definition,
                deprecated,
                whole_list_merge=whole_list_merge,
                array=True,
            )
        else:
            for i, subschema in enumerate(items):
                yield from get_schema_fields(
                    subschema,
                    f'{pointer}/items/{i}',
                    path_components,
                    definition,
                    deprecated,
                    whole_list_merge=whole_list_merge,
                    array=True,
                )

    for keyword in ('anyOf', 'allOf', 'oneOf'):
        if elements := schema.get(keyword):
            for i, subschema in enumerate(elements):
                # These keywords advance the pointer.
                yield from get_schema_fields(
                    subschema,
                    f'{pointer}/{keyword}/{i}',
                    path_components,
                    definition,
                    deprecated,
                    whole_list_merge=whole_list_merge,
                )

    for keyword in ('then', 'else'):
        if subschema := schema.get(keyword):
            # These keywords advance the pointer.
            yield from get_schema_fields(
                subschema,
                f'{pointer}/{keyword}',
                path_components,
                definition,
                deprecated,
                whole_list_merge=whole_list_merge,
            )

    if properties := schema.get('properties'):
        for name, subschema in properties.items():
            prop_pointer = f'{pointer}/properties/{name}'
            prop_path_components = (*path_components, name)
            prop_deprecated = _deprecated(subschema)
            prop_codelist, prop_open_codelist = _codelist(subschema)

            # To date, codelist and openCodelist in OCDS aren't set on `items`.
            yield Field(
                name=name,
                schema=subschema,
                pointer=prop_pointer,
                path_components=prop_path_components,
                definition=definition,
                deprecated_self=prop_deprecated,
                deprecated=deprecated or prop_deprecated,
                codelist=prop_codelist,
                open_codelist=prop_open_codelist,
                multilingual=name in multilingual,
                required=name in required,
                merge_by_id=name == 'id' and array and not whole_list_merge,
            )

            # `properties` advances the pointer and path.
            yield from get_schema_fields(
                subschema,
                prop_pointer,
                prop_path_components,
                definition,
                deprecated,
                whole_list_merge=whole_list_merge,
            )

    # Yield `patternProperties` after `properties`, to be interpreted in context.
    for name, subschema in nonmultilingual_pattern_properties.items():
        # The duplication across `properties` and `patternProperties` can be avoided, but is >5% slower.
        prop_pointer = f'{pointer}/patternProperties/{name}'
        prop_path_components = (*path_components, name)
        prop_deprecated = _deprecated(subschema)
        prop_codelist, prop_open_codelist = _codelist(subschema)

        yield Field(
            name=name,
            schema=subschema,
            pointer=prop_pointer,
            path_components=prop_path_components,
            definition=definition,
            deprecated_self=prop_deprecated,
            deprecated=deprecated or prop_deprecated,
            codelist=prop_codelist,
            open_codelist=prop_open_codelist,
            pattern=True,
            # `patternProperties` can't be multilingual, required, or "id".
        )

        # `patternProperties` advances the pointer and path.
        yield from get_schema_fields(
            subschema,
            prop_pointer,
            prop_path_components,
            definition,
            deprecated,
            whole_list_merge=whole_list_merge,
        )

    # `definitions` is canonically only at the top level.
    if not pointer:
        # Yield definitions after `properties` and `patternProperties`, to be interpreted in context.
        for keyword in ('definitions', '$defs'):
            if definitions := schema.get(keyword):
                for name, subschema in definitions.items():
                    # These keywords advance the pointer and set the definition.
                    yield from get_schema_fields(subschema, f'/{keyword}/{name}', definition=name)


def _codelist(subschema):
    default = 'enum' not in subschema
    if codelist := subschema.get('codelist'):
        return codelist, subschema.get('openCodelist', default)
    # The behavior hasn't been decided if `items` is an array (e.g. with conflicting codelist-related values).
    if (items := subschema.get('items')) and isinstance(items, dict):
        return items.get('codelist', ''), items.get('openCodelist', default)
    return '', default


def _deprecated(value):
    return value.get('deprecated') or (hasattr(value, '__reference__') and value.__reference__.get('deprecated')) or {}


def add_validation_properties(schema, *, unique_items=True, coordinates=False):
    """
    Add "minItems" and "uniqueItems" if an array, add "minProperties" if an object, and add "minLength" if a string
    and if "enum", "format" and "pattern" aren't set.

    :param dict schema: a JSON schema
    :param bool unique_items: whether to add "uniqueItems" properties to array fields
    :param bool coordinates: whether the parent is a geospatial coordinates field
    """
    if isinstance(schema, list):
        for item in schema:
            add_validation_properties(item, unique_items=unique_items)
    elif isinstance(schema, dict):
        if 'type' in schema:
            if (
                'string' in schema['type']
                # "enum" is more strict than "minLength".
                and 'enum' not in schema
                # The defined formats do not match zero-length strings.
                # https://datatracker.ietf.org/doc/html/draft-fge-json-schema-validation-00#section-7.3
                and 'format' not in schema
                # The pattern is assumed to not match zero-length strings.
                and 'pattern' not in schema
            ):
                schema.setdefault('minLength', 1)

            if 'array' in schema['type']:
                # Allow non-unique items for coordinates fields (e.g. closed polygons).
                if sorted(schema.get('items', {}).get('type', [])) == ['array', 'number']:
                    coordinates = True
                if unique_items and not coordinates:
                    schema.setdefault('uniqueItems', True)
                schema.setdefault('minItems', 1)

            if 'object' in schema['type']:
                schema.setdefault('minProperties', 1)

        for value in schema.values():
            add_validation_properties(value, unique_items=unique_items, coordinates=coordinates)
