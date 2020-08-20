import csv
import re

from ocdskit.exceptions import MissingColumnError
from ocdskit.schema import get_schema_fields

# See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def mapping_sheet(schema, io, order_by=None, infer_required=False, extension_field=None):
    """
    Writes information about all field paths in a JSON Schema to a CSV file.

    :param dict schema: a JSON schema
    :param io: a file-like object to which to write the rows
    :param str order_by: the column by which to sort the rows
    :param bool infer_required: whether to infer that a field is required if "null" is not in its ``type``
    :param str extension_field: the property in the JSON schema containing the name of the extension in which each
                                field was defined

    The CSV's columns are:

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
    :``links``: The URLs extracted from the field's ``description``
    :``deprecated``: The OCDS minor version in which the field (or its parent) was deprecated
    :``deprecationNotes``: The explanation for the deprecation of the field
    :``extension``: The name of the extension that introduced the JSON path (see the ``extension_field`` parameter)

    :raises MissingColumnError: if the column by which to order is missing
    """
    rows = []
    rows_by_path = {}
    for field in get_schema_fields(schema):
        if field.definition_pointer_components:
            continue

        prop = field.schema
        field.sep = '/'

        # If the field uses `$ref`, add an extra row for it. This makes it easier to use as a header for the object.
        # It also preserves the different titles and descriptions of the referrer and referee.
        if hasattr(prop, '__reference__'):
            reference = dict(prop.__reference__)
            prop = dict(prop)
            if extension_field in reference:
                prop[extension_field] = reference[extension_field]
            if 'type' not in reference and 'type' in prop:
                reference['type'] = prop['type']
            _add_row(rows, rows_by_path, field, reference, extension_field, infer_required=infer_required)

        _add_row(rows, rows_by_path, field, prop, extension_field, infer_required=infer_required)

        # If the field is an array, add an extra row for it. This makes it easier to use as a header for the object.
        if 'items' in prop and 'properties' in prop['items'] and 'title' in prop['items']:
            _add_row(rows, rows_by_path, field, prop['items'], extension_field, row={
                'path': field.path,
                'title': prop['items']['title'],
                'description': prop['items'].get('description', ''),
                'type': prop['items']['type'],
            })

    if order_by:
        try:
            rows.sort(key=lambda row: row[order_by])
        except KeyError:
            raise MissingColumnError("the column '{}' doesn't exist – did you make a typo?".format(order_by))

    fieldnames = ['section', 'path', 'title', 'description', 'type', 'range', 'values', 'links', 'deprecated',
                  'deprecationNotes']
    if extension_field:
        fieldnames.append(extension_field)

    w = csv.DictWriter(io, fieldnames)
    w.writeheader()
    w.writerows(rows)


def _add_row(rows, rows_by_path, field, schema, extension_field, *, infer_required=None, row=None):
    parent = rows_by_path.get(field.path_components[:-1], {})
    if not row:
        row = _make_row(field, schema, infer_required)

    if extension_field in schema:
        row['extension'] = schema[extension_field]
    elif 'extension' in parent:
        row['extension'] = parent['extension']

    rows.append(row)
    rows_by_path[field.path_components] = row


def _make_row(field, schema, infer_required):
    row = {
        'path': field.path,
        'title': schema.get('title', field.path_components[-1] + '*'),
        'deprecated': field.deprecated.get('deprecatedVersion'),  # deprecation from parent
    }

    if len(field.path_components) > 1:
        row['section'] = field.path_components[0]
    else:
        row['section'] = ''

    if 'description' in schema:
        links = dict(INLINE_LINK_RE.findall(schema['description']))
        row['description'] = schema['description']
        for key, link in links.items():
            row['description'] = row['description'].replace('[' + key + '](' + link + ')', key)
        row['links'] = ', '.join(links.values())

    required = False

    if 'type' in schema:
        if isinstance(schema['type'], str):
            type_ = [schema['type']]
        else:
            type_ = list(schema['type'])

        if 'null' in type_:
            type_.remove('null')
        elif infer_required:
            required = 'string' in type_ or 'integer' in type_

        row['type'] = ', '.join(type_)
    else:
        row['type'] = 'unknown'

    if field.required:
        required = True

    min_range = '1' if required else '0'
    max_range = 'n' if row['type'] == 'array' else '1'
    row['range'] = '{}..{}'.format(min_range, max_range)

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

    if 'deprecated' in schema:
        row['deprecated'] = schema['deprecated'].get('deprecatedVersion', '')
        row['deprecationNotes'] = schema['deprecated'].get('description', '')

    return row
