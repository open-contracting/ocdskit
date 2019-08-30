import copy
import csv
import re
from collections import OrderedDict

from ocdskit.exceptions import MissingColumnError
from ocdskit.schema import get_schema_fields

# See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def mapping_sheet(schema, output_stream, order_by=None, infer_required=False, extension_field=None):
    rows = []
    for field in get_schema_fields(schema):
        if field.definition_pointer_components:
            continue

        prop = field.schema
        field.sep = '/'

        # If the field uses `$ref`, add an extra row for it.
        if hasattr(prop, '__reference__'):
            reference = copy.copy(prop.__reference__)
            if 'type' not in reference and 'type' in prop:
                reference['type'] = prop['type']
            rows.append(_make_row(field, reference, infer_required, extension_field))

        rows.append(_make_row(field, prop, infer_required, extension_field))

        # If the field is an array, add an extra row for it.
        if 'items' in prop and 'properties' in prop['items'] and 'title' in prop['items']:
            rows.append({
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

    w = csv.DictWriter(output_stream, fieldnames)
    w.writeheader()
    w.writerows(rows)


def _make_row(field, schema, infer_required, extension_field):
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
        links = OrderedDict(INLINE_LINK_RE.findall(schema['description']))
        row['description'] = schema['description']
        for key, link in links.items():
            row['description'] = row['description'].replace('[' + key + '](' + link + ')', key)
        row['links'] = ', '.join(links.values())

    required = False

    if 'type' in schema:
        type_ = copy.copy(schema['type'])
        if 'null' in type_:
            type_.remove('null')
        elif infer_required:
            required = 'string' in type_ or 'integer' in type_

        if type(type_) in (tuple, list):
            row['type'] = ', '.join(type_)
        else:
            row['type'] = type_
    else:
        row['type'] = 'unknown'

    if field.required:
        required = True

    min_range = '1' if required else '0'
    max_range = 'n' if row['type'] == 'array' else '1'
    row['range'] = '{}..{}'.format(min_range, max_range)

    if 'format' in schema:
        row['values'] = schema['format']
    elif 'enum' in schema:
        values = copy.copy(schema['enum'])
        if None in values:
            values.remove(None)
        row['values'] = 'Enum: ' + ', '.join(values)
    elif 'items' in schema and 'enum' in schema['items']:
        values = copy.copy(schema['items']['enum'])
        if None in values:
            values.remove(None)
        row['values'] = 'Enum: ' + ', '.join(values)
    elif 'pattern' in schema:
        row['values'] = 'Pattern: ' + schema['pattern']
    else:
        row['values'] = ''

    if 'deprecated' in schema:
        row['deprecated'] = schema['deprecated'].get('deprecatedVersion', '')
        row['deprecationNotes'] = schema['deprecated'].get('description', '')

    if extension_field in schema:
        row['extension'] = schema[extension_field]

    return row
