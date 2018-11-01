import copy
import csv
import re
import sys
from collections import OrderedDict

from jsonref import JsonRef

from .base import BaseCommand


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths from an OCDS schema'

    def handle(self):
        release = self.json_load(self.buffer())

        release = JsonRef.replace_refs(release)

        # See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
        INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        def find_md_links(md):
            return OrderedDict(INLINE_LINK_RE.findall(md))

        def remove_links(text, links):
            for key, link in links.items():
                text = text.replace('[' + key + '](' + link + ')', key)
            return text

        def display_links(links):
            return ', '.join(links.values())

        def make_row(path, field, schema, deprecated, required_fields, is_reference=False):
            row = {'path': path+field, 'deprecated': deprecated}

            section = row['path'].split('/')[0] if '/' in row['path'] else ''

            row['section'] = section

            row['title'] = schema['title'] if 'title' in schema else field + '*'

            if 'description' in schema:
                links = find_md_links(schema['description'])
                row['description'] = remove_links(schema['description'], links)
                row['links'] = display_links(links)

            required = False

            # Type
            if 'type' in schema:
                # This checks whether this field is **implicity required**
                type_ = copy.copy(schema['type'])
                if 'null' in type_:
                    type_.remove('null')
                else:
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

            maxn = 'n' if row['type'] == 'array' else '1'
            minn = '1' if required else '0'
            row['range'] = minn + '..' + maxn

            # Format or restrictions
            if 'format' in schema:
                row['values'] = schema['format']
            elif 'enum' in schema:
                values = copy.copy(schema['enum'])
                if None in values:
                    values.remove(None)
                row['values'] = 'Codelist: ' + ', '.join(values)
            else:
                row['values'] = ''

            # Check for deprecation
            if 'deprecated' in schema:
                row['deprecated'] = schema['deprecated'].get('deprecatedVersion', '')
                row['deprecationNotes'] = schema['deprecated'].get('description', '')

            return row

        def display_properties(schema, path='', section='', deprecated=''):
            obj = schema['properties']
            required_fields = schema['required'] if 'required' in schema else []
            rows = []
            for field in obj:
                # If there was a reference, add an extra row for that
                if hasattr(obj[field], '__reference__'):
                    reference = copy.copy(obj[field].__reference__)
                    if 'type' not in reference and 'type' in obj[field]:
                        reference['type'] = obj[field]['type']
                    reference_row = make_row(
                        path, field, reference, deprecated, required_fields, is_reference=True)
                    rows.append(reference_row)
                else:
                    reference_row = {}

                row = make_row(path, field, obj[field], deprecated, required_fields)
                rows.append(row)

                children_deprecated = reference_row.get('deprecated') or reference_row.get('deprecated')

                if 'properties' in obj[field]:
                    rows = rows + display_properties(obj[field], path + field + '/', section, children_deprecated)

                if 'items' in obj[field]:
                    if 'properties' in obj[field]['items']:
                        if 'title' in obj[field]['items']:
                            rows.append({'section': section, 'path': path + field,
                                         'title': obj[field]['items']['title'],
                                         'description': obj[field]['items'].get('description', ''),
                                         'type': obj[field]['items']['type']})
                        else:
                            pass

                        rows = rows + display_properties(obj[field]['items'], path + field + '/', section,
                                                         row['deprecated'])

            return rows

        schema = display_properties(release)

        w = csv.DictWriter(sys.stdout, ['section', 'path', 'title', 'description', 'type', 'range', 'values', 'links',
                                        'deprecated', 'deprecationNotes'])
        w.writeheader()
        w.writerows(schema)
