import copy
import csv
import json
import re
import sys
from collections import OrderedDict

from jsonref import JsonRef

from .base import BaseCommand


class Command(BaseCommand):
    name = 'mapping-sheet'
    help = 'generates a spreadsheet with all field paths from an OCDS schema'

    def handle(self):
        release = json.load(self.buffer(), object_pairs_hook=OrderedDict)

        release = JsonRef.replace_refs(release)

        # See https://stackoverflow.com/questions/30734682/extracting-url-and-anchor-text-from-markdown-using-python
        INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        def find_md_links(md):
            return dict(INLINE_LINK_RE.findall(md))

        def remove_links(text, links):
            for key, link in links.items():
                text = text.replace('[' + key + '](' + link + ')', key)
            return text

        def display_links(links):
            return ', '.join(links.values())

        def display_properties(schema, path='', section='', deprecated=''):
            # Create a copy of obj, because there may be references to it from
            # elsewhere in the JSON schema, and we don't want to mutate it in
            # all those places
            obj = copy.deepcopy(schema['properties'])
            required_fields = schema['required'] if 'required' in schema else []
            rows = []
            for field in obj:
                row = {'path': path + field, 'deprecated': deprecated}

                section = row['path'].split('/')[0] if '/' in row['path'] else ''

                row['section'] = section

                # If there was a reference here, prefer the values from that
                if hasattr(obj[field], '__reference__'):
                    obj[field].update(obj[field].__reference__)

                row['title'] = obj[field]['title'] if 'title' in obj[field] else field + '*'

                if 'description' in obj[field]:
                    links = find_md_links(obj[field]['description'])
                    row['description'] = remove_links(obj[field]['description'], links)
                    row['links'] = display_links(links)

                # Type
                if 'type' in obj[field]:
                    # ToDo: Add checking of the required array also.
                    # This checks whether this field is **implicity required**
                    if 'null' in obj[field]['type']:
                        obj[field]['type'].remove('null')
                        required = False
                    else:
                        required = 'string' in obj[field]['type'] or 'integer' in obj[field]['type']

                    if type(obj[field]['type']) in (tuple, list):
                        row['type'] = ', '.join(obj[field]['type'])
                    else:
                        row['type'] = obj[field]['type']
                else:
                    row['type'] = 'unknown'

                # Required field
                if field in required_fields:
                    required = True

                maxn = 'n' if row['type'] == 'array' else '1'
                minn = '1' if required else '0'
                row['range'] = minn + '..' + maxn

                # Format or restrictions
                if 'format' in obj[field]:
                    row['values'] = obj[field]['format']
                elif 'enum' in obj[field]:
                    if None in obj[field]['enum']:
                        obj[field]['enum'].remove(None)
                    row['values'] = 'Codelist: ' + ', '.join(obj[field]['enum'])
                else:
                    row['values'] = ''

                # Check for deprecation
                if 'deprecated' in obj[field]:
                    row['deprecated'] = obj[field]['deprecated'].get('deprecatedVersion', '')
                    row['deprecationNotes'] = obj[field]['deprecated'].get('description', '')

                rows.append(row)

                if 'properties' in obj[field]:
                    rows = rows + display_properties(obj[field], path + field + '/', section, row['deprecated'])

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
