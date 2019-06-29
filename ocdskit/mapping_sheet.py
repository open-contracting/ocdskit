import copy
import csv
import os.path
import pathlib
import re
from collections import OrderedDict

import jsonref

from ocdskit.exceptions import MissingColumnError

# See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


class MappingSheet:
    def run(self, input_filename, output_stream, order_by=None, infer_required=False):
        self.infer_required = infer_required

        with open(input_filename) as f:
            schema = jsonref.load(f, object_pairs_hook=OrderedDict,
                                  base_uri=pathlib.Path(os.path.realpath(input_filename)).as_uri())

        rows = self.display_properties(schema)
        if order_by:
            try:
                rows.sort(key=lambda row: row[order_by])
            except KeyError:
                raise MissingColumnError("the column '{}' doesn't exist – did you make a typo?".format(order_by))

        w = csv.DictWriter(output_stream, ['section', 'path', 'title', 'description', 'type', 'range', 'values',
                                           'links', 'deprecated', 'deprecationNotes'])
        w.writeheader()
        w.writerows(rows)

    def make_row(self, path, field, schema, deprecated, required_fields, is_reference=False):
        row = {
            'path': path + field,
            'title': schema.get('title', field + '*'),
            'deprecated': deprecated,  # deprecation from parent
        }

        row['section'] = row['path'].split('/')[0] if '/' in row['path'] else ''

        if 'description' in schema:
            links = OrderedDict(INLINE_LINK_RE.findall(schema['description']))
            row['description'] = schema['description']
            for key, link in links.items():
                row['description'] = row['description'].replace('[' + key + '](' + link + ')', key)
            row['links'] = ', '.join(links.values())

        required = False

        # Type
        if 'type' in schema:
            # This checks whether this field is **implicity required**
            type_ = copy.copy(schema['type'])
            if 'null' in type_:
                type_.remove('null')
            elif self.infer_required:
                required = 'string' in type_ or 'integer' in type_

            if type(type_) in (tuple, list):
                row['type'] = ', '.join(type_)
            else:
                row['type'] = type_
        else:
            row['type'] = 'unknown'

        # This checks whether this field is **explicitly required**
        if field in required_fields:
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

        return row

    def display_properties(self, schema, path='', section='', deprecated=''):
        obj = schema['properties']

        required_fields = schema.get('required', [])

        rows = []

        for field in obj:
            # If there was a reference, add an extra row for that
            if hasattr(obj[field], '__reference__'):
                reference = copy.copy(obj[field].__reference__)
                if 'type' not in reference and 'type' in obj[field]:
                    reference['type'] = obj[field]['type']
                reference_row = self.make_row(path, field, reference, deprecated, required_fields, is_reference=True)

                rows.append(reference_row)
            else:
                reference_row = {}

            row = self.make_row(path, field, obj[field], deprecated, required_fields)
            rows.append(row)

            children_deprecated = reference_row.get('deprecated')

            if 'properties' in obj[field]:
                rows += self.display_properties(obj[field], path + field + '/', section, children_deprecated)

            if 'items' in obj[field]:
                if 'properties' in obj[field]['items']:
                    if 'title' in obj[field]['items']:
                        rows.append({
                            'section': section,
                            'path': path + field,
                            'title': obj[field]['items']['title'],
                            'description': obj[field]['items'].get('description', ''),
                            'type': obj[field]['items']['type'],
                        })

                    rows += self.display_properties(obj[field]['items'], path + field + '/', section,
                                                    row['deprecated'])

        return rows
