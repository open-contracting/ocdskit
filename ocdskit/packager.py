import json
from collections import defaultdict
from itertools import groupby
from tempfile import NamedTemporaryFile

from ocdskit.exceptions import InconsistentVersionError
from ocdskit.util import (_empty_record_package, _remove_empty_optional_metadata, _set_extensions_metadata,
                          _update_package_metadata, get_ocds_minor_version, is_release, json_dumps)

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


class Packager:
    """
    The Packager context manager helps to build a single record package, or a stream of compiled releases or merged
    releases. Release packages and/or individual releases can be added to the packager. All releases should use the
    same version of OCDS.
    """
    def __enter__(self):
        self.package = _empty_record_package()
        self.version = None

        if using_sqlite:
            self.backend = SQLiteBackend()
        else:
            self.backend = PythonBackend()

        return self

    def __exit__(self, type, value, traceback):
        self.backend.close()

    def add(self, data):
        """
        Adds release packages and/or individual releases to be merged.

        :param data: an iterable of release packages and individual releases
        """
        for i, item in enumerate(data):
            version = get_ocds_minor_version(item)
            if self.version:
                if version != self.version:
                    # OCDS 1.1 and OCDS 1.0 have different merge rules for `awards.suppliers`. Also, mixing new and
                    # deprecated fields can lead to inconsistencies (e.g. transaction `amount` and `value`).
                    # https://standard.open-contracting.org/latest/en/schema/changelog/#advisories
                    raise InconsistentVersionError('item {}: version error: this item uses version {}, but earlier '
                                                   'items used version {}'.format(i, version, self.version),
                                                   self.version, version)
            else:
                self.version = version

            if is_release(item):
                self.backend.add_release(item['ocid'], '', item)
            else:  # release package
                uri = item.get('uri', '')

                _update_package_metadata(self.package, item)

                # Note: If there are millions of packages to merge, we should use SQLite to store the packages instead.
                if uri:
                    self.package['packages'].append(uri)

                for release in item['releases']:
                    self.backend.add_release(release['ocid'], uri, release)

            self.backend.flush()

    def output_package(self, merger, return_versioned_release=False, use_linked_releases=False):
        """
        Yields a record package.

        :param ocdsmerge.merge.Merger merger: a merger
        :param bool return_versioned_release: whether to include versioned releases in the record package
        :param bool use_linked_releases: whether to use linked releases instead of full releases, if possible
        """
        for ocid, rows in self.backend.get_releases_by_ocid():
            record = {
                'ocid': ocid,
                'releases': [],
            }

            releases = []
            for ocid, uri, release in rows:
                releases.append(release)

                if use_linked_releases and uri:
                    package_release = {
                        'url': uri + '#' + release['id'],
                        'date': release['date'],
                        'tag': release['tag'],
                    }
                else:
                    package_release = release
                record['releases'].append(package_release)

            # Note: An optimization would be for OCDS Merge to create both merged releases at once (i.e. flatten once).
            record['compiledRelease'] = merger.create_compiled_release(releases)
            if return_versioned_release:
                record['versionedRelease'] = merger.create_versioned_release(releases)

            self.package['records'].append(record)

        _set_extensions_metadata(self.package)
        _remove_empty_optional_metadata(self.package)

        yield self.package

    def output_releases(self, merger, return_versioned_release=False):
        """
        Yields compiled releases or versioned releases, ordered by OCID.

        :param ocdsmerge.merge.Merger merger: a merger
        :param bool return_versioned_release: whether to yield versioned releases instead of compiled releases
        """
        for ocid, rows in self.backend.get_releases_by_ocid():
            releases = (row[2] for row in rows)

            if return_versioned_release:
                yield merger.create_versioned_release(releases)
            else:
                yield merger.create_compiled_release(releases)


# The backend's responsibilities (for now) are exclusively to:
#
# * Group releases by OCID
# * Store each release's package URI
class AbstractBackend:
    def __init__(self):
        """
        Initializes the backend.
        """
        raise NotImplementedError

    def add_release(self, ocid, package_uri, release):
        """
        Adds a release to the backend. (The release might be added to an internal buffer.)
        """
        raise NotImplementedError

    def get_releases_by_ocid(self):
        """
        Yields an OCIDs and an iterable of tuples of ``(ocid, package_uri, release)``.

        OCIDs are yielded in alphabetical order. The iterable is in any order.
        """
        raise NotImplementedError

    def flush(self):
        """
        Flushes the internal buffer of releases. This may be a no-op on some backends.
        """
        pass

    def close(self):
        """
        Tidies up any resources used by the backend. This may be a no-op on some backends.
        """
        pass


class PythonBackend(AbstractBackend):
    def __init__(self):
        self.groups = defaultdict(list)

    def add_release(self, ocid, uri, release):
        self.groups[ocid].append((ocid, uri, release))

    def get_releases_by_ocid(self):
        for ocid in sorted(self.groups):
            yield ocid, self.groups[ocid]


class SQLiteBackend(AbstractBackend):
    # "The sqlite3 module internally uses a statement cache to avoid SQL parsing overhead."
    # https://docs.python.org/3.7/library/sqlite3.html#sqlite3.connect
    # Note: We never commit changes. SQLite manages the memory usage of uncommitted changes.
    # https://sqlite.org/atomiccommit.html#_cache_spill_prior_to_commit
    def __init__(self):
        self.file = NamedTemporaryFile()

        self.connection = sqlite3.connect(self.file.name, detect_types=sqlite3.PARSE_DECLTYPES)

        # Disable unnecessary, expensive features.
        # https://www.sqlite.org/pragma.html#pragma_synchronous
        # https://www.sqlite.org/pragma.html#pragma_journal_mode
        self.connection.execute('PRAGMA synchronous=OFF')
        self.connection.execute('PRAGMA journal_mode=OFF')

        self.connection.execute("CREATE TABLE releases (ocid text, uri text, release json)")

        self.buffer = []

    def add_release(self, ocid, uri, release):
        self.buffer.append((ocid, uri, release))

    def flush(self):
        self.connection.executemany("INSERT INTO releases VALUES (?, ?, ?)", self.buffer)

        self.buffer = []

    def get_releases_by_ocid(self):
        # It is faster to insert the rows then create the index, than the reverse.
        # https://stackoverflow.com/questions/1711631/improve-insert-per-second-performance-of-sqlite
        self.connection.execute("CREATE INDEX ocid_idx ON releases(ocid)")

        results = self.connection.execute("SELECT * FROM releases ORDER BY ocid")
        for ocid, rows in groupby(results, lambda row: row[0]):
            yield ocid, rows

    def close(self):
        self.file.close()
        self.connection.close()
