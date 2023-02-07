import re

import jsonref

from ocdskit.exceptions import MissingColumnError
from ocdskit.schema import get_schema_fields
from ocdskit.util import _cast_as_list

# See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def mapping_sheet(schema, order_by=None, infer_required=False, extension_field=None, inherit_extension=True,
                  include_codelist=False, include_deprecated=True, include_definitions=False, base_uri=None):
    """
    Returns information about all field paths in a JSON Schema, as columns and rows.

    If ``include_definitions=False``, this function resolves ``$ref`` properties.

    :param dict schema: a JSON schema
    :param str order_by: the column by which to sort the rows
    :param bool infer_required: whether to infer that a field is required if "null" is not in its ``type``
    :param str extension_field: the property in the JSON schema containing the name of the extension in which each
                                field was defined
    :param bool inherit_extension: whether fields defined via $ref properties inherit the "extension" value of their
                                parent field
    :param bool include_codelist: whether to include a "codelist" column
    :param bool include_deprecated: whether to include any deprecated fields
    :param bool include_definitions: whether to traverse the "definitions" property
    :param str base_uri: the URL to resolve relative references against
    :returns: information about all field paths in a JSON Schema, as columns and rows
    :rtype: tuple

    The columns are:

    :``section``: The first part of the JSON path to the field in the data, e.g. ``tender``
    :``path``: The JSON path to the field in the data, e.g. ``tender/id``
    :``title``: The field's ``title`` in the JSON schema.  If the field has no ``title``, defaults to the field's name
      followed by "*".
    :``description``: The field's ``description`` in the JSON schema. URLs are removed (see the ``links`` column).
    :``type``: A comma-separated list of the field's ``type`` in the JSON schema, excluding "null". If the field has no
      ``type``, defaults to "unknown".
    :``range``: The field's allowed number of occurrences.

      * "0..1" if the field defines an optional literal value.
      * "0..n" if the field defines an optional array.
      * "1..1" if the field defines a required literal value.
      * "1..n" if the field defines a required array.
    :``values``: If the field's schema sets:

      * ``format``: the ``format``
      * ``pattern``: the ``pattern``
      * ``enum``: "Enum: " followed by the ``enum`` as a comma-separated list, excluding ``null``
      * ``items/enum``: "Enum: " followed by the ``items/enum`` as a comma-separated list, excluding ``null``
    :``codelist``: The field's ``codelist`` in the JSON schema
    :``links``: The URLs extracted from the field's ``description``
    :``deprecated``: The OCDS minor version in which the field (or its parent) was deprecated
    :``deprecationNotes``: The explanation for the deprecation of the field
    :``extension``: The name of the extension that introduced the JSON path (see the ``extension_field`` parameter)

    :raises MissingColumnError: if the column by which to order is missing
    """
    kwargs = {
        'inherit_extension': inherit_extension,
        'include_codelist': include_codelist,
        'include_deprecated': include_deprecated,
    }

    if not include_definitions:
        # jsonref.JsonRef is deprecated, but used for backwards-compatibility with jsonref 0.x.
        schema = jsonref.JsonRef.replace_refs(schema, base_uri=base_uri, jsonschema=True)

    rows = []
    rows_by_path = {}
    for field in get_schema_fields(schema):
        if not include_definitions and field.definition_pointer_components:
            continue

        prop = field.schema
        field.sep = '/'
        extension_name = prop.get(extension_field)

        # If the schema sets a `$ref` property, add an extra row for it. This preserves any differences in the titles
        # and descriptions of the referrer and referee. The new row can be formatted as a heading for the object.
        if hasattr(prop, '__reference__'):
            reference = dict(prop.__reference__)
            prop = dict(prop)
            if extension_field in reference:
                extension_name = reference[extension_field]
            if 'type' not in reference and 'type' in prop:
                reference['type'] = prop['type']
            _add_row(rows, rows_by_path, field, reference, extension_name, infer_required=infer_required,
                     **kwargs)

        _add_row(rows, rows_by_path, field, prop, extension_name, infer_required=infer_required,
                 **kwargs)

        # If the field is an array, add an extra row for it. This makes it easier to use as a header for the object.
        if 'items' in prop and 'properties' in prop['items'] and 'title' in prop['items']:
            row = {
                'path': field.path,
                'title': prop['items']['title'],
                'description': prop['items'].get('description', ''),
                'type': prop['items']['type'],
                'deprecated': field.deprecated.get('deprecatedVersion'),  # deprecation from parent
            }
            _add_deprecated(row, prop['items'])

            _add_row(rows, rows_by_path, field, prop['items'], extension_name, row=row, **kwargs)

    if order_by:
        try:
            rows.sort(key=lambda row: row[order_by])
        except KeyError as e:
            raise MissingColumnError(f"the column '{order_by}' doesn't exist – did you make a typo?") from e

    columns = ['section', 'path', 'title', 'description', 'type', 'range', 'values', 'links', 'deprecated',
               'deprecationNotes']
    if extension_field:
        columns.append('extension')
    if include_codelist:
        columns.append('codelist')

    return columns, rows


def _add_deprecated(row, schema):
    # OCDS for PPPs sets `"deprecated": null`.
    if schema.get('deprecated'):
        row['deprecated'] = schema['deprecated'].get('deprecatedVersion', '')
        row['deprecationNotes'] = schema['deprecated'].get('description', '')


def _add_row(rows, rows_by_path, field, schema, extension_name, *, infer_required=None, inherit_extension=True,
             include_codelist=False, include_deprecated=True, row=None):
    parent = rows_by_path.get(field.path_components[:-1], {})
    if not row:
        row = _make_row(field, schema, infer_required, include_codelist)

    if extension_name:
        row['extension'] = extension_name
    elif 'extension' in parent and inherit_extension:
        row['extension'] = parent['extension']

    if include_deprecated or not row['deprecated']:
        rows.append(row)

    rows_by_path[field.path_components] = row


def _make_row(field, schema, infer_required, include_codelist):
    row = {
        'path': field.path,
        'title': schema.get('title', field.path_components[-1] + '*'),
        'deprecated': field.deprecated.get('deprecatedVersion'),  # deprecation from parent
    }

    if len(field.path_components) > 1:
        row['section'] = field.path_components[0]
    else:
        row['section'] = field.definition_path

    if 'description' in schema:
        links = dict(INLINE_LINK_RE.findall(schema['description']))
        row['description'] = schema['description']
        for key, link in links.items():
            row['description'] = row['description'].replace('[' + key + '](' + link + ')', key)
        row['links'] = ', '.join(links.values())

    required = False

    if 'type' in schema:
        types = _cast_as_list(schema['type'])

        if 'null' in types:
            types.remove('null')
        elif infer_required:
            required = 'string' in types or 'integer' in types

        row['type'] = ', '.join(types)
    else:
        row['type'] = 'unknown'

    if field.required:
        required = True

    min_range = '1' if required else '0'
    max_range = 'n' if row['type'] == 'array' else '1'
    row['range'] = f'{min_range}..{max_range}'

    if 'format' in schema:
        row['values'] = schema['format']
    elif 'pattern' in schema:
        row['values'] = 'Pattern: ' + schema['pattern']
    elif 'enum' in schema:
        values = list(schema['enum'])
        if None in values:
            values.remove(None)
        row['values'] = 'Enum: ' + ', '.join(values)
    elif 'items' in schema and 'enum' in schema['items']:
        values = list(schema['items']['enum'])
        if None in values:
            values.remove(None)
        row['values'] = 'Enum: ' + ', '.join(values)
    else:
        row['values'] = ''

    if include_codelist:
        row['codelist'] = schema.get('codelist')

    _add_deprecated(row, schema)

    return row
