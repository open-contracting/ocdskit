import json
from collections import defaultdict
from itertools import groupby
from tempfile import NamedTemporaryFile

from ocdsextensionregistry import ProfileBuilder
from ocdsmerge import Merger
from ocdsmerge.util import get_release_schema_url, get_tags

from ocdskit.exceptions import InconsistentVersionError
from ocdskit.util import get_ocds_minor_version, is_package, json_dumps

try:
    import sqlite3
    using_sqlite = True

    def adapt_json(d):
        return json_dumps(d)

    def convert_json(s):
        return json.loads(s)

    sqlite3.register_adapter(dict, adapt_json)
    sqlite3.register_converter('json', convert_json)
except ImportError:
    using_sqlite = False


def _package(key, items, uri, publisher, published_date, extensions):
    if publisher is None:
        publisher = {}
    if 'name' not in publisher:
        publisher['name'] = ''
    if extensions is None:
        extensions = []

    output = {
        'uri': uri,
        'publisher': publisher,
        'publishedDate': published_date,
        'version': '1.1',
        'extensions': extensions,
        key: items,
    }

    return output


def package_records(records, uri='', publisher=None, published_date='', extensions=None):
    """
    Wraps records in a record package.

    :param list records: a list of records
    :param str uri: the record package's ``uri``
    :param dict publisher: the record package's ``publisher``
    :param str published_date: the record package's ``publishedDate``
    :param list extensions: the record package's ``extensions``
    """
    return _package('records', records, uri, publisher, published_date, extensions)


def package_releases(releases, uri='', publisher=None, published_date='', extensions=None):
    """
    Wraps releases in a release package.

    :param list releases: a list of releases
    :param str uri: the release package's ``uri``
    :param dict publisher: the release package's ``publisher``
    :param str published_date: the release package's ``publishedDate``
    :param list extensions: the release package's ``extensions``
    """
    return _package('releases', releases, uri, publisher, published_date, extensions)


def combine_record_packages(packages, uri='', publisher=None, published_date=''):
    """
    Collects the packages and records from the record packages into one record package.

    :param list packages: a list of record packages
    :param str uri: the record package's ``uri``
    :param dict publisher: the record package's ``publisher``
    :param str published_date: the record package's ``publishedDate``
    """
    if publisher is None:
        publisher = {}

    output = {
        'uri': uri,
        'publisher': publisher,
        'publishedDate': published_date,
        'license': None,
        'publicationPolicy': None,
        'version': None,
        'extensions': {},
        'packages': [],
        'records': [],
    }

    for package in packages:
        _update_package_metadata(output, package, publisher)

        output['records'].extend(package['records'])

        if 'packages' in package:
            output['packages'].extend(package['packages'])

    if not output['packages']:
        del output['packages']

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def combine_release_packages(packages, uri='', publisher=None, published_date=''):
    """
    Collects the releases from the release packages into one release package.

    :param list packages: a list of release packages
    :param str uri: the release package's ``uri``
    :param dict publisher: the release package's ``publisher``
    :param str published_date: the release package's ``publishedDate``
    """
    if publisher is None:
        publisher = {}

    output = {
        'uri': uri,
        'publisher': publisher,
        'publishedDate': published_date,
        'license': None,
        'publicationPolicy': None,
        'version': None,
        'extensions': {},
        'releases': [],
    }

    for package in packages:
        _update_package_metadata(output, package, publisher)

        output['releases'].extend(package['releases'])

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def compile_release_packages(data, uri='', publisher=None, published_date='', schema=None,
                             return_versioned_release=False, return_package=False, use_linked_releases=False):
    """
    Merges releases by OCID and yields compiled releases.

    If ``return_versioned_release`` is ``True``, yields the versioned release. If ``return_package`` is ``True``, wraps
    the compiled releases (and versioned releases if ``return_versioned_release`` is ``True``) in a record package.

    If ``return_package`` is set and ``publisher`` isn't set, the output record package will have the same publisher as
    the last input release package.

    :param list data: a list of release packages and individual releases
    :param str uri: if ``return_package`` is ``True``, the record package's ``uri``
    :param dict publisher: if ``return_package`` is ``True``, the record package's ``publisher``
    :param str published_date: if ``return_package`` is ``True``, the record package's ``publishedDate``
    :param dict schema: the URL or path of the release schema to use
    :param bool return_package: wrap the compiled releases in a record package
    :param bool use_linked_releases: if ``return_package`` is ``True``, use linked releases instead of full releases if
        the input is a release package
    :param bool return_versioned_release: if ``return_package`` is ``True``, include versioned releases in the record
        package; otherwise, yield versioned releases instead of compiled releases
    """
    if return_package:
        output = {
            'uri': uri,
            'publisher': publisher,
            'publishedDate': published_date,
            'license': None,
            'publicationPolicy': None,
            'version': None,
            'extensions': {},
            'packages': [],
            'records': [],
        }
    # To avoid duplicating code, we track extensions in the same place even if ``return_package`` is false.
    else:
        output = {
            'extensions': {},
        }

    version = None
    linked_releases = []

    try:
        if using_sqlite:
            file = NamedTemporaryFile()

            # "The sqlite3 module internally uses a statement cache to avoid SQL parsing overhead."
            # https://docs.python.org/3.7/library/sqlite3.html#sqlite3.connect
            # Note: We never commit changes. SQLite manages the memory usage of uncommitted changes.
            # https://sqlite.org/atomiccommit.html#_cache_spill_prior_to_commit
            conn = sqlite3.connect(file.name, detect_types=sqlite3.PARSE_DECLTYPES)

            # Disable unnecessary, expensive features.
            # https://www.sqlite.org/pragma.html#pragma_synchronous
            # https://www.sqlite.org/pragma.html#pragma_journal_mode
            conn.execute('PRAGMA synchronous=OFF')
            conn.execute('PRAGMA journal_mode=OFF')

            conn.execute("CREATE TABLE releases (ocid text, release json)")
        else:
            releases_by_ocid = defaultdict(list)

        for i, item in enumerate(data):
            packaged = is_package(item)

            if not version:
                version = get_ocds_minor_version(item)
            else:
                v = get_ocds_minor_version(item)
                if v != version:
                    raise InconsistentVersionError('item {}: version error: this item uses version {}, but earlier '
                                                   'items used version {}'.format(i, v, version), version, v)

            if not schema:
                prefix = version.replace('.', '__') + '__'
                tag = next(tag for tag in reversed(get_tags()) if tag.startswith(prefix))
                schema = get_release_schema_url(tag)

            if using_sqlite:
                values = []

            if packaged:
                releases = item['releases']
            else:
                releases = [item]

            for release in releases:
                if using_sqlite:
                    values.append((release['ocid'], release))
                else:
                    releases_by_ocid[release['ocid']].append(release)

                if return_package and use_linked_releases:
                    if packaged:
                        release = {
                            'url': item['uri'] + '#' + release['id'],
                            'date': release['date'],
                            'tag': release['tag'],
                        }
                    linked_releases.append(release)

            if using_sqlite:
                conn.executemany("INSERT INTO releases VALUES (?, ?)", values)

            if packaged:
                if return_package:
                    _update_package_metadata(output, item, publisher)

                    output['packages'].append(item['uri'])
                else:
                    _update_extensions_metadata(output, item)

        if output['extensions']:
            builder = ProfileBuilder(tag, list(output['extensions']))
            schema = builder.patched_release_schema()

        merger = Merger(schema)

        if using_sqlite:
            # It is faster to insert the rows then create the index, than the reverse.
            # https://stackoverflow.com/questions/1711631/improve-insert-per-second-performance-of-sqlite
            conn.execute("CREATE INDEX ocid_idx ON releases(ocid)")

            def iterator():
                results = conn.execute("SELECT * FROM releases ORDER BY ocid")
                for ocid, rows in groupby(results, lambda row: row[0]):
                    yield ocid, (row[1] for row in rows)
        else:
            def iterator():
                for ocid in sorted(releases_by_ocid):
                    yield ocid, releases_by_ocid[ocid]

        if return_package:
            for ocid, releases in iterator():
                releases = list(releases)  # need a list, not a generator, as we'll iterate over it many times

                record = {
                    'ocid': ocid,
                    'releases': [],
                    'compiledRelease': merger.create_compiled_release(releases),
                }

                if use_linked_releases:
                    record['releases'] = linked_releases
                else:
                    record['releases'] = releases

                if return_versioned_release:
                    record['versionedRelease'] = merger.create_versioned_release(releases)

                output['records'].append(record)

            _set_extensions_metadata(output)
            _remove_empty_optional_metadata(output)

            yield output
        else:
            for ocid, releases in iterator():
                if return_versioned_release:
                    yield merger.create_versioned_release(releases)
                else:
                    yield merger.create_compiled_release(releases)
    finally:
        if using_sqlite:
            file.close()
            conn.close()


def _update_package_metadata(output, package, publisher):
    _update_extensions_metadata(output, package)

    if not publisher and 'publisher' in package:
        output['publisher'] = package['publisher']

    for field in ('license', 'publicationPolicy', 'version'):
        if field in package:
            output[field] = package[field]


def _update_extensions_metadata(output, package):
    if 'extensions' in package:
        # We use an insertion-ordered dict to keep extensions in order without duplication.
        output['extensions'].update(dict.fromkeys(package['extensions']))


def _set_extensions_metadata(output):
    if output['extensions']:
        output['extensions'] = list(output['extensions'])
    else:
        del output['extensions']


def _remove_empty_optional_metadata(output):
    for field in ('license', 'publicationPolicy', 'version'):
        if output[field] is None:
            del output[field]
