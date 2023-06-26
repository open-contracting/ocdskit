from dataclasses import dataclass, field

LANGUAGE_CODE_SUFFIX = '_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+))'  # noqa: E501
LANGUAGE_CODE_SUFFIX_LEN = len(LANGUAGE_CODE_SUFFIX)


def _join_sep(sep, words):
    return sep + sep.join(words)


@dataclass
class Field:
    """
    Initializes a schema field object.
    """

    #: the field's schema
    schema: dict = None
    #: the JSON pointer to the field in the schema, e.g. ``('properties', 'tender', 'properties', 'id')``
    pointer_components: tuple = None
    #: the path to the field in data, e.g. ``('tender', 'id')``
    path_components: tuple = None
    #: the JSON pointer to the definition in which the field is defined, e.g. ``('definitions', 'Item')``
    definition_pointer_components: tuple = None
    #: the path to the definition in which the field is defined, e.g. ``('Item')``
    definition_path_components: tuple = None
    #: whether the field is listed in the schema's ``required``
    required: bool = None
    #: if the field, or an ancestor of the field, sets ``deprecated``, the ``deprecated`` object
    deprecated: dict = field(default_factory=dict)
    #: whether the field has a corresponding field in the schema's ``patternProperties``
    multilingual: bool = None
    #: the separator to use in string representations of paths
    sep = '.'

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    @property
    def pointer(self):
        """
        Returns the JSON pointer to the field in the schema, e.g. ``/properties/tender/properties/id``.
        """
        return _join_sep('/', self.pointer_components)

    @property
    def definition_pointer(self):
        """
        Returns the JSON pointer to the definition in which the field is defined, e.g. ``/definitions/Item``.
        """
        return _join_sep('/', self.definition_pointer_components)

    @property
    def path(self):
        """
        Returns the path to the field in data with ``self.sep`` as separator, e.g. ``tender.id``.
        """
        return self.sep.join(self.path_components)

    @property
    def definition_path(self):
        """
        Returns the path to the definition in which the field is defined with ``self.sep`` as separator, e.g. ``Item``.
        """
        return self.sep.join(self.definition_path_components)

    def __repr__(self):
        return repr(self.asdict())

    def asdict(self, sep=None, exclude=None):
        """
        Returns the field as a dict, with keys for: ``schema``, ``pointer``, ``path``,
        ``definition_pointer``, ``definition_path``, ``required``, ``deprecated``, ``multilingual``.

        :param list sep: the separator to use in string representations of paths, overriding ``self.sep``
        :param list exclude: a list of keys to exclude from the dict
        """
        data = {}

        exclude = exclude or ()
        sep = sep or self.sep

        for key, value in self.__dict__.items():
            if key not in exclude and not key.startswith('_') and not key.endswith('_components'):
                data[key] = value
        for key in ('pointer', 'definition_pointer'):
            if key not in exclude:
                data[key] = getattr(self, key)
        for key in ('path', 'definition_path'):
            if key not in exclude:
                data[key] = sep.join(getattr(self, f'{key}_components'))

        return data


# This code is similar to `add_versioned` in `make_versioned_release_schema.py` in the `standard` repository.
def get_schema_fields(schema, pointer=None, path=None, definition_pointer=None, definition_path=None, deprecated=None):
    """
    Yields a ``Field`` object for each field (whether under ``properties`` or ``patternProperties``) in a JSON schema.

    :param dict schema: a JSON schema
    :param tuple pointer: the JSON pointer to the field in the schema, e.g.
                          ``('properties', 'tender', 'properties', 'id')``
    :param tuple path: the path to the field in data, e.g.
                       ``('tender', 'id')``
    :param tuple definition_pointer: the JSON pointer to the definition in which the field is defined, e.g.
                                     ``('definitions', 'Item')``
    :param tuple definition_path: the path to the definition in which the field is defined, e.g.
                                  ``('Item')``
    :param dict deprecated: if the field, or an ancestor of the field, sets ``deprecated``, the ``deprecated``
                            object
    """
    if pointer is None:
        pointer = ()
    if path is None:
        path = ()
    if definition_pointer is None:
        definition_pointer = ()
    if definition_path is None:
        definition_path = ()

    multilingual = set()
    hidden = set()
    for key, value in schema.get('patternProperties', {}).items():
        # The pattern might have an extra set of parentheses.
        for offset in (2, 1):
            end = -LANGUAGE_CODE_SUFFIX_LEN - offset
            # The pattern must be anchored and the suffix must occur at the end.
            if (
                key[end:-offset] == LANGUAGE_CODE_SUFFIX
                and key[:offset] == '^('[:offset]
                and key[-offset:] == ')$'[-offset:]
            ):
                multilingual.add(key[offset:end])
                hidden.add(key)
                break

    for key, value in schema.get('properties', {}).items():
        new_pointer = pointer + ('properties', key)
        new_path = path + (key,)
        required = schema.get('required', [])
        yield from _get_schema_field(key, value, new_pointer, new_path, definition_pointer, definition_path,
                                     required, deprecated or _deprecated(value), multilingual)

    for key, value in schema.get('definitions', {}).items():
        new_pointer = pointer + ('definitions', key)
        yield from get_schema_fields(value, pointer=new_pointer, path=(), definition_pointer=new_pointer,
                                     definition_path=(key,), deprecated=deprecated)

    for key, value in schema.get('patternProperties', {}).items():
        if key not in hidden:
            new_pointer = pointer + ('patternProperties', key)
            new_path = path + (f'({key})',)
            yield Field(schema=value, pointer_components=new_pointer, path_components=new_path,
                        definition_pointer_components=definition_pointer, definition_path_components=definition_path,
                        required=False, deprecated=deprecated or _deprecated(value), multilingual=False)


def _get_schema_field(name, schema, pointer, path, definition_pointer, definition_path, required, deprecated,
                      multilingual):
    yield Field(schema=schema, pointer_components=pointer, path_components=path,
                definition_pointer_components=definition_pointer, definition_path_components=definition_path,
                required=name in required, deprecated=deprecated, multilingual=name in multilingual)

    if schema is None:
        return

    if 'properties' in schema or 'patternProperties' in schema:
        yield from get_schema_fields(schema, pointer=pointer, path=path, definition_pointer=definition_pointer,
                                     definition_path=definition_path, deprecated=deprecated)

    for key, value in schema.get('items', {}).get('properties', {}).items():
        new_pointer = pointer + ('items', 'properties', key)
        new_path = path + (key,)
        required = schema['items'].get('required', [])
        yield from _get_schema_field(key, value, new_pointer, new_path, definition_pointer, definition_path,
                                     required, deprecated or _deprecated(value), multilingual)


def _deprecated(value):
    if value is None:
        return {}
    return value.get('deprecated') or hasattr(value, '__reference__') and value.__reference__.get('deprecated') or {}


def add_validation_properties(schema, unique_items=True, coordinates=False):
    """
    Adds "minItems" and "uniqueItems" if an array, adds "minProperties" if an object, and adds "minLength" if a string
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
