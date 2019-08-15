LANGUAGE_CODE_SUFFIX = '_(((([A-Za-z]{2,3}(-([A-Za-z]{3}(-[A-Za-z]{3}){0,2}))?)|[A-Za-z]{4}|[A-Za-z]{5,8})(-([A-Za-z]{4}))?(-([A-Za-z]{2}|[0-9]{3}))?(-([A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-([0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(x(-[A-Za-z0-9]{1,8})+))?)|(x(-[A-Za-z0-9]{1,8})+))'  # noqa
LANGUAGE_CODE_SUFFIX_LEN = len(LANGUAGE_CODE_SUFFIX)


# This code is similar to `add_versioned` in `make_versioned_release_schema.py` in the `standard` repository.
def get_schema_fields(schema, pointer=None, path=None, definition_pointer=None, definition_path=None, deprecated=None):
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
            if key[end:-offset] == LANGUAGE_CODE_SUFFIX and key[:offset] == '^('[:offset] and key[-offset:] == ')$'[-offset:]:  # noqa
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
            new_path = path[:-1] + (path[-1] + '({})'.format(key),)
            yield {'definition_pointer': definition_pointer, 'definition_path': definition_path,
                   'pointer': new_pointer, 'path': new_path, 'schema': value, 'required': False,
                   'deprecated': deprecated or _deprecated(value), 'multilingual': False}


def _get_schema_field(name, schema, pointer, path, definition_pointer, definition_path, required, deprecated,
                      multilingual):
    yield {'definition_pointer': definition_pointer, 'definition_path': definition_path,
           'pointer': pointer, 'path': path, 'schema': schema, 'required': name in required,
           'deprecated': deprecated, 'multilingual': name in multilingual}

    if schema and ('properties' in schema or 'patternProperties' in schema):
        yield from get_schema_fields(schema, pointer=pointer, path=path, definition_pointer=definition_pointer,
                                     definition_path=definition_path, deprecated=deprecated)

    for key, value in schema.get('items', {}).get('properties', {}).items():
        new_pointer = pointer + ('items', 'properties', key)
        new_path = path + (key,)
        required = schema['items'].get('required', [])
        yield from _get_schema_field(key, value, new_pointer, new_path, definition_pointer, definition_path,
                                     required, deprecated or _deprecated(value), multilingual)


def _deprecated(value):
    return value.get('deprecated') or hasattr(value, '__reference__') and value.__reference__.get('deprecated') or {}
