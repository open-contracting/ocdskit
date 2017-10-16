import json
import argparse
import sqlalchemy as sa
import jsonref
import ocdsmerge
import collections
import sys
from sqlalchemy.dialects.postgresql import JSONB


def process_schema_object(path, current_name, flattened, obj):
    properties = obj['properties']
    current_object = flattened.get(path)
    if current_object is None:
        current_object = {}
        flattened[path] = current_object

    for name, property in list(properties.items()):
        prop_type = property['type']
        if prop_type == 'object':
            flattened = process_schema_object(path, current_name + name + '_', flattened, property)
            # flattened = process_schema_object(path + (name,), '', flattened, property)
        elif prop_type == 'array':
            if property['items']['type'] != 'object':
                current_object[current_name + name] = property['items']['type'] + '[]'
            else:
                flattened = process_schema_object(path + (current_name + name,), '', flattened, property['items'])
        else:
            current_object[current_name + name] = prop_type

    return flattened


def create_db(sqlalchemy_url, deref_schema, drop=False):
    engine = sa.create_engine(sqlalchemy_url)
    metadata = sa.MetaData(engine)

    if drop:
        metadata.reflect()
        for table in reversed(metadata.sorted_tables):
            table.drop()
        metadata = sa.MetaData(engine)

    flattened = {}
    flat = process_schema_object((), '', flattened, deref_schema)
    for table, fields in flat.items():
        table_name = "_".join(table)
        if not table_name:
            table_name = 'releases'
        columns = [sa.Column('ocid', sa.Text)]
        for parent_table in ('releases',) + table:
            columns.append(sa.Column(parent_table[:-1] + '_id', sa.Text))
            # columns.append(sa.Column(parent_table + '_id', sa.Text))

        for field in sorted(fields.keys()):
            types = fields[field]
            if field == 'id':
                continue
            if 'string' in types:
                columns.append(sa.Column(field, sa.Text))
            elif 'number' in types:
                columns.append(sa.Column(field, sa.Numeric))
            elif 'integer' in types:
                columns.append(sa.Column(field, sa.Integer))
            else:
                columns.append(sa.Column(field, sa.Text))
        if 'postgresql' in engine.name:
            columns.append(sa.Column('extras', JSONB))
        else:
            columns.append(sa.Column('extras', sa.Text))

        sa.Table(table_name, metadata, *columns)

    metadata.create_all(engine)
    return metadata, engine


def process_object(path, current_name, current_keys, flattened, obj, flat_obj):
    if flat_obj is None:
        flat_list = flattened.get(path)
        if flat_list is None:
            flat_list = []
            flattened[path] = flat_list
        new_id = obj.pop('id', None)
        # new_id = obj.get('id', None)
        if not new_id:
            new_id = str(len(flat_list) + 1)
        if not current_keys:
            current_keys = (obj['ocid'],)
        current_keys = current_keys + (new_id,)
        flat_obj = {'ocid': current_keys[0]}
        for num, table in enumerate(('releases',) + path):
            flat_obj[table[:-1] + '_id'] = current_keys[num + 1]
            # flat_obj[table + '_id'] = current_keys[num + 1]
        flat_list.append(flat_obj)

    for key, value in obj.items():
        if isinstance(value, dict):
            process_object(path, current_name + key + '_', current_keys, flattened, value, flat_obj)
            # process_object(path + (key,), '', current_keys, flattened, value, None)
        elif isinstance(value, list):
            if not value:
                continue
            if isinstance(value[0], dict):
                for item in value:
                    process_object(path + (current_name + key,), '', current_keys, flattened, item, None)
                    # process_object(path + (key,), '', current_keys, flattened, item, None)
            else:
                flat_obj[current_name + key] = json.dumps(value)
        else:
            flat_obj[current_name + key] = value
    return flattened


def upload_files(metadata, engine, deref_schema, files, merge=False):
    releases = []
    if merge:
        all_releases = collections.defaultdict(list)
        for file in files:
            with open(file) as document:
                json_document = json.loads(document.read())
                if 'releases' not in json_document:
                    print("If you select --merge then all the packages have to be release packages, exiting...")
                    sys.exit(0)
                for release in json_document['releases']:
                    all_releases[release['ocid']].append(release)
        releases = []
        for release_list in all_releases.values():
            releases.append(ocdsmerge.merge(release_list))
        upload_file(metadata, engine, deref_schema, releases)
    else:
        for file in files:
            with open(file) as document:
                json_document = json.loads(document.read())
                if 'releases' in json_document:
                    releases = json_document["releases"]
                elif 'records' in json_document:
                    releases = []
                    for record in json_document['records']:
                        releases.append(record['compiledRelease'])
            upload_file(metadata, engine, deref_schema, releases)


def upload_file(metadata, engine, deref_schema, releases):
    conn = engine.connect()

    tabulated = {}
    for release in releases:
        tabulated = process_object(tuple(), '', tuple(), tabulated, release, None)

    for table, rows in tabulated.items():
        if not table:
            table_name = 'releases'
        else:
            table_name = '_'.join(table)
        try:
            table = metadata.tables[table_name]
        except KeyError:
            print("table {} does not exist".format(table_name))
            continue

        for row in rows:
            for key in table.c.keys():
                if key not in row.keys():
                    row[key] = None
            extras = {}
            for key in list(row.keys()):
                if key not in table.c:
                    extras[key] = row.pop(key)
            if 'postgresql' in engine.name:
                row['extras'] = extras
            else:
                row['extras'] = json.dumps(extras)
        conn.execute(table.insert(), rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get some ocds data tabularized')
    parser.add_argument('database_url',
                        help='sqlalchemy database url')
    parser.add_argument('files', help='json files to upload to db', nargs='+')
    parser.add_argument('--merge', help='say if you want to ocds merge the files', action='store_true')
    parser.add_argument('--drop', help='drop all current tables', action='store_true')
    parser.add_argument('--schema_url', help='schema file used', default='http://ocds.open-contracting.org/standard/r'
                                                                         '/1__0__0/release-schema.json')
    args = parser.parse_args()

    deref_schema = jsonref.load_uri(args.schema_url)

    metadata, engine = create_db(args.database_url, deref_schema, drop=args.drop)

    upload_files(metadata, engine, deref_schema, args.files, args.merge)
