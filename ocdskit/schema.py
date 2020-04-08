LANGUAGE_CODE_SUFFIX = '_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+))'  # noqa: E501
LANGUAGE_CODE_SUFFIX_LEN = len(LANGUAGE_CODE_SUFFIX)


def _join_sep(sep, words):
    return sep + sep.join(words)


class Field:
    def __init__(self, schema=None, pointer=None, path=None, definition_pointer=None, definition_path=None,
                 required=None, deprecated=None, multilingual=None, sep='.'):
        """
        Initializes a schema field object.

        :param dict schema: the field's schema
        :param tuple pointer: the JSON pointer to the field in the schema, e.g.
                              ``('properties', 'tender', 'properties', 'id')``
        :param tuple path: the path to the field in data, e.g.
                           ``('tender', 'id')``
        :param tuple definition_pointer: the JSON pointer to the definition in which the field is defined, e.g.
                                         ``('definitions', 'Item')``
        :param tuple definition_path: the path to the definition in which the field is defined, e.g.
                                      ``('Item')``
        :param bool required: whether the field is listed in the schema's ``required``
        :param dict deprecated: if the field, or an ancestor of the field, sets ``deprecated``, the ``deprecated``
                                object
        :param bool multilingual: whether the field has a corresponding field in the schema's ``patternProperties``
        :param str sep: the separator to use in string representations of paths
        """
        self.schema = schema
        self.pointer_components = pointer
        self.path_components = path
        self.definition_pointer_components = definition_pointer
        self.definition_path_components = definition_path
        self.required = required
        self.deprecated = deprecated
        self.multilingual = multilingual
        self._sep = sep

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
        return self._sep.join(self.path_components)

    @property
    def definition_path(self):
        """
        Returns the path to the definition in which the field is defined with ``self.sep`` as separator, e.g. ``Item``.
        """
        return self._sep.join(self.definition_path_components)

    @property
    def sep(self):
        """
        Returns the separator to use in string representations of paths.
        """
        return self._sep

    @sep.setter
    def sep(self, sep):
        """
        Sets the separator to use in string representations of paths.
        """
        self._sep = sep

    def __repr__(self):
        return repr(self.asdict())

    def asdict(self, sep=None, exclude=None):
        """
        Returns the field as a dict, with keys for: ``schema``, ``pointer``, ``path``,
        ``definition_pointer``, ``definition_path``, ``required``, ``deprecated``, ``multilingual``.

        :param list sep: the separator to use in string representations of paths, overriding ``self.sep``
        :param list exclude: a list of keys to exclude from the dict
        """
        d = {}

        exclude = exclude or ()
        sep = sep or self.sep

        for k, v in self.__dict__.items():
            if k not in exclude and not k.startswith('_') and not k.endswith('_components'):
                d[k] = v
        for k in ('pointer', 'definition_pointer'):
            if k not in exclude:
                d[k] = getattr(self, k)
        for k in ('path', 'definition_path'):
            if k not in exclude:
                d[k] = sep.join(getattr(self, '{}_components'.format(k)))

        return d


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
            if (key[end:-offset] == LANGUAGE_CODE_SUFFIX and
                    key[:offset] == '^('[:offset] and key[-offset:] == ')$'[-offset:]):
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
            new_path = path + ('({})'.format(key),)
            yield Field(schema=value, pointer=new_pointer, path=new_path, definition_pointer=definition_pointer,
                        definition_path=definition_path, required=False, deprecated=deprecated or _deprecated(value),
                        multilingual=False)


def _get_schema_field(name, schema, pointer, path, definition_pointer, definition_path, required, deprecated,
                      multilingual):
    yield Field(schema=schema, pointer=pointer, path=path, definition_pointer=definition_pointer,
                definition_path=definition_path, required=name in required, deprecated=deprecated,
                multilingual=name in multilingual)

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
