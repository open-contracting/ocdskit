import copy
import csv
import re
from collections import OrderedDict

from ocdskit.exceptions import MissingColumnError

# See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


class MappingSheet:
    def run(self, schema, output_stream, order_by=None, infer_required=False):
        self.infer_required = infer_required

        rows = list(self.traverse(schema))
        if order_by:
            try:
                rows.sort(key=lambda row: row[order_by])
            except KeyError:
                raise MissingColumnError("the column '{}' doesn't exist – did you make a typo?".format(order_by))

        w = csv.DictWriter(output_stream, ['section', 'path', 'title', 'description', 'type', 'range', 'values',
                                           'links', 'deprecated', 'deprecationNotes'])
        w.writeheader()
        w.writerows(rows)

    def make_row(self, path, field, schema, deprecated, required_fields):
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

        if 'type' in schema:
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

    def traverse(self, schema, path='', section='', deprecated=''):
        properties = schema.get('properties', {})
        required = schema.get('required', [])

        for field, prop in properties.items():
            # If there was a reference, add an extra row for that
            if hasattr(prop, '__reference__'):
                reference = copy.copy(prop.__reference__)
                if 'type' not in reference and 'type' in prop:
                    reference['type'] = prop['type']
                reference_row = self.make_row(path, field, reference, deprecated, required)
                yield reference_row
            else:
                reference_row = {}

            row = self.make_row(path, field, prop, deprecated, required)
            yield row

            children_deprecated = reference_row.get('deprecated', row['deprecated'])
            if 'properties' in prop:
                yield from self.traverse(prop, path + field + '/', section, children_deprecated)

            if 'items' in prop and 'properties' in prop['items']:
                if 'title' in prop['items']:
                    yield {
                        'section': section,
                        'path': path + field,
                        'title': prop['items']['title'],
                        'description': prop['items'].get('description', ''),
                        'type': prop['items']['type'],
                    }

                yield from self.traverse(prop['items'], path + field + '/', section, row['deprecated'])
