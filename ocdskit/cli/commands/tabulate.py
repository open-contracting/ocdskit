import jsonref
import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB

from ocdskit.cli.commands.base import OCDSCommand
from ocdskit.util import is_record, is_record_package, is_release_package, json_dumps


class Command(OCDSCommand):
    name = 'tabulate'
    help = 'load packages into a database'

    def add_arguments(self):
        self.add_argument('database_url', help='a SQLAlchemy database URL')
        self.add_argument('--drop', help='drop all tables before loading', action='store_true')
        self.add_argument('--schema', help='the release-schema.json to use',
                          default='https://standard.open-contracting.org/latest/en/release-schema.json')

    def handle(self):
        deref_schema = jsonref.load_uri(self.args.schema)
        metadata, engine = self.create_db(self.args.database_url, deref_schema, drop=self.args.drop)

        for i, data in enumerate(self.items()):
            if is_record_package(data):
                releases = []
                for record in data['records']:
                    releases.extend(record['releases'])
            elif is_release_package(data) or is_record(data):
                releases = data['releases']
            else:  # release
                releases = [data]

            self.upload_file(metadata, engine, deref_schema, releases)

    def process_schema_object(self, path, current_name, flattened, obj):
        """
        Return a dictionary with a flattened representation of the schema. `patternProperties` are skipped as we don't
        want them as field names (a regular expression string) in the database.
        """
        properties = obj.get('properties', {})  # an object may have patternProperties only
        current_object = flattened.get(path)

        if current_object is None:
            current_object = {}
            flattened[path] = current_object

        for name, prop in list(properties.items()):
            prop_type = prop['type']
            if prop_type == 'object':
                flattened = self.process_schema_object(path, current_name + name + '_', flattened, prop)
            elif prop_type == 'array':
                if 'object' not in prop['items']['type']:
                    current_object[current_name + name] = prop['items']['type'] + '[]'
                else:
                    flattened = self.process_schema_object(path + (current_name + name,), '', flattened, prop['items'])
            else:
                current_object[current_name + name] = prop_type

        return flattened

    def create_db(self, sqlalchemy_url, deref_schema, drop=False):
        engine = sqlalchemy.create_engine(sqlalchemy_url)
        metadata = sqlalchemy.MetaData(engine)

        if drop:
            metadata.reflect()
            for table in reversed(metadata.sorted_tables):
                table.drop()
            metadata = sqlalchemy.MetaData(engine)

        flattened = {}
        flat = self.process_schema_object((), '', flattened, deref_schema)

        for table, fields in flat.items():
            table_name = '_'.join(table)
            if not table_name:
                table_name = 'releases'
            columns = [sqlalchemy.Column('ocid', sqlalchemy.Text)]
            for parent_table in ('releases',) + table:
                columns.append(sqlalchemy.Column(parent_table[:-1] + '_id', sqlalchemy.Text))

            for field in sorted(fields.keys()):
                types = fields[field]
                if field == 'id':
                    continue
                if 'string' in types:
                    columns.append(sqlalchemy.Column(field, sqlalchemy.Text))
                elif 'number' in types:
                    columns.append(sqlalchemy.Column(field, sqlalchemy.Numeric))
                elif 'integer' in types:
                    columns.append(sqlalchemy.Column(field, sqlalchemy.Integer))
                else:
                    columns.append(sqlalchemy.Column(field, sqlalchemy.Text))
            if 'postgresql' in engine.name:
                columns.append(sqlalchemy.Column('extras', JSONB))
            else:
                columns.append(sqlalchemy.Column('extras', sqlalchemy.Text))

            sqlalchemy.Table(table_name, metadata, *columns)

        metadata.create_all(engine)
        return metadata, engine

    def process_object(self, path, current_name, current_keys, flattened, obj, flat_obj):
        if flat_obj is None:
            flat_list = flattened.get(path)
            if flat_list is None:
                flat_list = []
                flattened[path] = flat_list
            new_id = obj.pop('id', None)
            if not new_id:
                new_id = str(len(flat_list) + 1)
            if not current_keys:
                current_keys = (obj['ocid'],)
            current_keys = current_keys + (new_id,)
            flat_obj = {'ocid': current_keys[0]}
            for num, table in enumerate(('releases',) + path):
                flat_obj[table[:-1] + '_id'] = current_keys[num + 1]
            flat_list.append(flat_obj)

        for key, value in obj.items():
            if isinstance(value, dict):
                self.process_object(path, current_name + key + '_', current_keys, flattened, value, flat_obj)
            elif isinstance(value, list):
                if not value:
                    continue
                if isinstance(value[0], dict):
                    for item in value:
                        self.process_object(path + (current_name + key,), '', current_keys, flattened, item, None)
                else:
                    flat_obj[current_name + key] = json_dumps(value)
            else:
                flat_obj[current_name + key] = value
        return flattened

    def upload_file(self, metadata, engine, deref_schema, releases):
        conn = engine.connect()

        tabulated = {}
        for release in releases:
            tabulated = self.process_object(tuple(), '', tuple(), tabulated, release, None)

        for table, rows in tabulated.items():
            if not table:
                table_name = 'releases'
            else:
                table_name = '_'.join(table)
            try:
                table = metadata.tables[table_name]
            except KeyError:
                print('table {} does not exist'.format(table_name))
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
                    row['extras'] = json_dumps(extras)
            conn.execute(table.insert(), rows)
