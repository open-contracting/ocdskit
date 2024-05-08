import itertools
import os
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from tempfile import NamedTemporaryFile
from typing import Union

import ocdsmerge
from ocdsmerge.exceptions import InconsistentTypeError

from ocdskit.exceptions import InconsistentVersionError, MergeErrorWarning, MissingOcidKeyError
from ocdskit.util import (
    _empty_record_package,
    _remove_empty_optional_metadata,
    _resolve_metadata,
    _update_package_metadata,
    get_ocds_minor_version,
    is_release,
    json_dumps,
    jsonlib,
)

try:
    import sqlite3

    USING_SQLITE = True

    def adapt_json(data):
        return json_dumps(data)

    def convert_json(string):
        return jsonlib.loads(string)

    sqlite3.register_adapter(dict, adapt_json)
    sqlite3.register_converter('json', convert_json)
except ImportError:
    USING_SQLITE = False


# The `warnings.catch_warnings()` context manager resets the `showwarning` method to the module's definition.
# Accept a `showwarning` method as an argument, to preserve any earlier override (e.g. by `__main__.py`).
def _showwarning(showwarning, ocid):
    def function(message, category, filename, lineno, file=None, line=None):
        showwarning(f"{ocid}: {message}", category, filename, lineno, file=file, line=line)

    return function


class Packager:
    """
    The Packager context manager helps to build a single record package, or a stream of compiled releases or merged
    releases. Release packages and/or individual releases can be added to the packager. All releases should use the
    same version of OCDS.
    """

    def __init__(self, force_version: Union[str, None] = None):
        """
        :param force_version: version to use instead of the version of the first release package or individual release
        """
        self.package = _empty_record_package()
        self.version = force_version

        if USING_SQLITE:
            self.backend = SQLiteBackend()
        else:
            self.backend = PythonBackend()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.backend.close()

    def add(self, data, ignore_version: bool = False):
        """
        Adds release packages and/or individual releases to be merged.

        :param data: an iterable of release packages and individual releases
        :param ignore_version: do not raise an error if the versions are inconsistent across items to merge
        :raises InconsistentVersionError: if the versions are inconsistent across items to merge
        """
        for i, item in enumerate(data):
            version = get_ocds_minor_version(item)
            if self.version:
                if not ignore_version and version != self.version:
                    # OCDS 1.1 and OCDS 1.0 have different merge rules for `awards.suppliers`. Also, mixing new and
                    # deprecated fields can lead to inconsistencies (e.g. transaction `amount` and `value`).
                    # https://standard.open-contracting.org/latest/en/schema/changelog/#advisories
                    raise InconsistentVersionError(
                        f'item {i}: version error: this item uses version {version}, '
                        f'but earlier items used version {self.version}',
                        self.version,
                        version,
                    )
            else:
                self.version = version

            if is_release(item):
                self.backend.add_release(item, '')
            else:  # release package
                uri = item.get('uri', '')

                _update_package_metadata(self.package, item)

                # Note: If there are millions of packages to merge, we should use SQLite to store the packages instead.
                if uri and version < '1.2':
                    self.package['packages'].append(uri)

                for release in item['releases']:
                    if release is not None:  # observed in some release packages
                        self.backend.add_release(release, uri)

            self.backend.flush()

    def output_package(
        self,
        merger: ocdsmerge.merge.Merger,
        return_versioned_release: bool = False,
        use_linked_releases: bool = False,
        streaming: bool = False,
        convert_exceptions_to_warnings: bool = False,
    ):
        """
        Yields a record package.

        :param merger: a merger
        :param return_versioned_release: whether to include a versioned release in each record
        :param use_linked_releases: whether to use linked releases instead of full releases, if possible
        :param streaming: whether to set the package's records to a generator instead of a list
        :param convert_exceptions_to_warnings: whether to convert inconsistent type errors from OCDS Merge to warnings
        """
        records = self.output_records(
            merger,
            return_versioned_release=return_versioned_release,
            use_linked_releases=use_linked_releases,
            convert_exceptions_to_warnings=convert_exceptions_to_warnings,
        )

        # If a user wants to stream data but can’t exhaust records right away, we can add an `autoclose=True` argument.
        # If set to `False`, `__exit__` will do nothing, and the user will need to call `packager.backend.close()`.
        if not streaming:
            records = list(records)

        self.package['records'] = records

        _resolve_metadata(self.package, 'packages')
        _resolve_metadata(self.package, 'extensions')
        _remove_empty_optional_metadata(self.package)

        yield self.package

    def output_records(
        self,
        merger: ocdsmerge.merge.Merger,
        return_versioned_release: bool = False,
        use_linked_releases: bool = False,
        convert_exceptions_to_warnings: bool = False,
    ):
        """
        Yields records, ordered by OCID.

        :param merger: a merger
        :param return_versioned_release: whether to include a versioned release in the record
        :param use_linked_releases: whether to use linked releases instead of full releases, if possible
        :param convert_exceptions_to_warnings: whether to convert inconsistent type errors from OCDS Merge to warnings
        """
        for ocid, rows in self.backend.get_releases_by_ocid():
            record = {
                'ocid': ocid,
                'releases': [],
            }

            releases = []
            for _, uri, release in rows:
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

            showwarning = warnings.showwarning
            with warnings.catch_warnings():
                warnings.showwarning = _showwarning(showwarning, ocid)

                try:
                    record['compiledRelease'] = merger.create_compiled_release(releases)
                    if return_versioned_release:
                        record['versionedRelease'] = merger.create_versioned_release(releases)
                except InconsistentTypeError as e:
                    if convert_exceptions_to_warnings:
                        warnings.warn(MergeErrorWarning(e))
                    else:
                        raise

            yield record

    def output_releases(
        self,
        merger: ocdsmerge.merge.Merger,
        return_versioned_release: bool = False,
        convert_exceptions_to_warnings: bool = False,
    ):
        """
        Yields compiled releases or versioned releases, ordered by OCID.

        :param merger: a merger
        :param return_versioned_release: whether to yield versioned releases instead of compiled releases
        :param convert_exceptions_to_warnings: whether to convert inconsistent type errors from OCDS Merge to warnings
        """
        for ocid, rows in self.backend.get_releases_by_ocid():
            releases = (row[-1] for row in rows)

            showwarning = warnings.showwarning
            with warnings.catch_warnings():
                warnings.showwarning = _showwarning(showwarning, ocid)

                try:
                    if return_versioned_release:
                        yield merger.create_versioned_release(releases)
                    else:
                        yield merger.create_compiled_release(releases)
                except InconsistentTypeError as e:
                    if convert_exceptions_to_warnings:
                        warnings.warn(MergeErrorWarning(e))
                    else:
                        raise


# The backend's responsibilities (for now) are exclusively to:
#
# * Group releases by OCID
# * Store each release's package URI
#
# For a PostgreSQL backend, see https://github.com/open-contracting/ocdskit/issues/116
class AbstractBackend(ABC):
    def add_release(self, release, package_uri):
        """
        Adds a release to the backend. (The release might be added to an internal buffer.)

        :raises MissingOcidKeyError: if the release is missing an ``ocid`` field
        """
        try:
            self._add_release(release['ocid'], package_uri, release)
        except KeyError as e:
            raise MissingOcidKeyError('ocid') from e

    @abstractmethod
    def _add_release(self, ocid, package_uri, release):
        pass

    @abstractmethod
    def get_releases_by_ocid(self):
        """
        Yields an OCIDs and an iterable of tuples of ``(ocid, package_uri, release)``.

        OCIDs are yielded in alphabetical order. The iterable is in any order.
        """

    def flush(self):
        """
        Flushes the internal buffer of releases. This may be a no-op on some backends.
        """

    def close(self):
        """
        Tidies up any resources used by the backend. This may be a no-op on some backends.
        """


class PythonBackend(AbstractBackend):
    def __init__(self):
        self.groups = defaultdict(list)

    def _add_release(self, ocid, package_uri, release):
        self.groups[ocid].append((ocid, package_uri, release))

    def get_releases_by_ocid(self):
        for ocid in sorted(self.groups):
            yield ocid, self.groups[ocid]


class SQLiteBackend(AbstractBackend):
    # "The sqlite3 module internally uses a statement cache to avoid SQL parsing overhead."
    # https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
    # Note: We never commit changes. SQLite manages the memory usage of uncommitted changes.
    # https://sqlite.org/atomiccommit.html#_cache_spill_prior_to_commit
    def __init__(self):
        self.file = NamedTemporaryFile(delete=False)

        # https://docs.python.org/3/library/sqlite3.html#sqlite3.PARSE_DECLTYPES
        self.connection = sqlite3.connect(self.file.name, detect_types=sqlite3.PARSE_DECLTYPES)

        # https://sqlite.org/tempfiles.html#temp_databases
        self.connection.execute("CREATE TEMP TABLE releases (ocid text, uri text, release json)")

        self.buffer = []

    def _add_release(self, ocid, package_uri, release):
        self.buffer.append((ocid, package_uri, release))

    def flush(self):
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.executemany
        self.connection.executemany("INSERT INTO releases VALUES (?, ?, ?)", self.buffer)

        self.buffer = []

    def get_releases_by_ocid(self):
        self.connection.execute("CREATE INDEX IF NOT EXISTS ocid_idx ON releases(ocid)")

        results = self.connection.execute("SELECT * FROM releases ORDER BY ocid")
        yield from itertools.groupby(results, lambda row: row[0])

    def close(self):
        self.file.close()
        self.connection.close()
        os.unlink(self.file.name)
