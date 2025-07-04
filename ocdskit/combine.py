from __future__ import annotations

import warnings

from ocdsextensionregistry import ProfileBuilder
from ocdsmerge import Merger
from ocdsmerge.util import get_release_schema_url

from ocdskit.exceptions import MissingRecordsWarning, MissingReleasesWarning
from ocdskit.packager import Packager
from ocdskit.util import (
    _empty_record_package,
    _empty_release_package,
    _remove_empty_optional_metadata,
    _resolve_metadata,
    _update_package_metadata,
    get_ocds_patch_tag,
)

DEFAULT_VERSION = '1.1'  # fields might be deprecated


def _package(key, items, uri, publisher, published_date, version, extensions=None):
    if publisher is None:
        publisher = {}
    publisher.setdefault('name', '')

    output = {
        'uri': uri,
        'publisher': publisher,
        'publishedDate': published_date,
        'version': version,
    }

    if extensions:
        output['extensions'] = extensions

    output[key] = items

    return output


def package_records(records, uri='', publisher=None, published_date='', version=DEFAULT_VERSION, extensions=None):
    """
    Wrap records in a record package.

    :param list records: a list of records
    :param str uri: the record package's ``uri``
    :param dict publisher: the record package's ``publisher``
    :param str published_date: the record package's ``publishedDate``
    :param str version: the record package's ``version``
    :param list extensions: the record package's ``extensions``
    """
    return _package('records', records, uri, publisher, published_date, version, extensions)


def package_releases(releases, uri='', publisher=None, published_date='', version=DEFAULT_VERSION, extensions=None):
    """
    Wrap releases in a release package.

    :param list releases: a list of releases
    :param str uri: the release package's ``uri``
    :param dict publisher: the release package's ``publisher``
    :param str published_date: the release package's ``publishedDate``
    :param str version: the release package's ``version``
    :param list extensions: the release package's ``extensions``
    """
    return _package('releases', releases, uri, publisher, published_date, version, extensions)


def combine_record_packages(packages, uri='', publisher=None, published_date='', version=DEFAULT_VERSION):
    """
    Collect the packages and records from the record packages into one record package.

    Warn ``~ocdskit.exceptions.MissingRecordsWarning`` if the "records" field is missing from a record package.

    :param packages: an iterable of record packages
    :param str uri: the record package's ``uri``
    :param dict publisher: the record package's ``publisher``
    :param str published_date: the record package's ``publishedDate``
    :param str version: the record package's ``version``
    """
    # See options for not buffering all inputs into memory: https://github.com/open-contracting/ocdskit/issues/119
    output = _empty_record_package(uri, publisher, published_date, version)
    output['packages'] = {}

    for i, package in enumerate(packages):
        _update_package_metadata(output, package)
        if 'records' in package:
            output['records'].extend(package['records'])
        else:
            warnings.warn(
                f'item {i} has no "records" field (check that it is a record package)',
                category=MissingRecordsWarning,
                stacklevel=2,
            )
        if 'packages' in package:
            output['packages'].update(dict.fromkeys(package['packages']))

    if publisher:
        output['publisher'] = publisher

    _resolve_metadata(output, 'packages')
    _resolve_metadata(output, 'extensions')
    _remove_empty_optional_metadata(output)

    return output


def combine_release_packages(packages, uri='', publisher=None, published_date='', version=DEFAULT_VERSION):
    """
    Collect the releases from the release packages into one release package.

    Warn ``~ocdskit.exceptions.MissingReleasesWarning`` if the "releases" field is missing from a release package.

    :param packages: an iterable of release packages
    :param str uri: the release package's ``uri``
    :param dict publisher: the release package's ``publisher``
    :param str published_date: the release package's ``publishedDate``
    :param str version: the release package's ``version``
    """
    # See options for not buffering all inputs into memory: https://github.com/open-contracting/ocdskit/issues/119
    output = _empty_release_package(uri, publisher, published_date, version)

    for i, package in enumerate(packages):
        _update_package_metadata(output, package)
        if 'releases' in package:
            output['releases'].extend(package['releases'])
        else:
            warnings.warn(
                f'item {i} has no "releases" field (check that it is a release package)',
                category=MissingReleasesWarning,
                stacklevel=2,
            )

    if publisher:
        output['publisher'] = publisher

    _resolve_metadata(output, 'extensions')
    _remove_empty_optional_metadata(output)

    return output


def merge(
    data,
    uri: str = '',
    publisher: dict | None = None,
    published_date: str = '',
    version: str = DEFAULT_VERSION,
    schema: dict | None = None,
    *,
    return_versioned_release: bool = False,
    return_package: bool = False,
    use_linked_releases: bool = False,
    streaming: bool = False,
    force_version: str | None = None,
    ignore_version: bool = False,
    convert_exceptions_to_warnings: bool = False,
):
    """
    Merge release packages and individual releases.

    By default, yields compiled releases. If ``return_versioned_release`` is ``True``, yields versioned releases. If
    ``return_package`` is ``True``, wraps the compiled releases (and versioned releases if ``return_versioned_release``
    is ``True``) in a record package.

    If ``return_package`` is set and ``publisher`` isn't set, the output record package will have the same publisher as
    the last input release package.

        .. attention::

           This function is vulnerable to server-side request forgery (SSRF). A user can create a release package or
           record package whose extension URLs point to internal resources, which would receive a GET request.

    :param data: an iterable of release packages and individual releases
    :param uri: if ``return_package`` is ``True``, the record package's ``uri``
    :param publisher: if ``return_package`` is ``True``, the record package's ``publisher``
    :param published_date: if ``return_package`` is ``True``, the record package's ``publishedDate``
    :param version: if ``return_package`` is ``True``, the record package's ``version``
    :param schema: the URL, path or dict of the patched release schema to use
    :param return_package: wrap the compiled releases in a record package
    :param use_linked_releases: if ``return_package`` is ``True``, use linked releases instead of full releases,
        if the input is a release package
    :param return_versioned_release: if ``return_package`` is ``True``, include versioned releases in the record
        package; otherwise, yield versioned releases instead of compiled releases
    :param streaming: if ``return_package`` is ``True``, set the package's records to a generator (this only works
        if the calling code exhausts the generator before ``merge`` returns)
    :param force_version: version to use instead of the version of the first release package or individual release
    :param ignore_version: do not raise an error if the versions are inconsistent across items to merge
    :param convert_exceptions_to_warnings: whether to convert inconsistent type errors from OCDS Merge to warnings
    :raises InconsistentVersionError: if the versions are inconsistent across items to merge
    :raises MissingOcidKeyError: if the release is missing an ``ocid`` field
    :raises UnknownVersionError: if the OCDS version is not recognized
    """
    with Packager(force_version=force_version) as packager:
        packager.add(data, ignore_version=ignore_version)

        if not schema and packager.version:
            tag = get_ocds_patch_tag(packager.version)
            if packager.package['extensions']:
                # `extensions` is an insertion-ordered dict at this point.
                builder = ProfileBuilder(tag, list(packager.package['extensions']))
                schema = builder.patched_release_schema()
            else:
                schema = get_release_schema_url(tag)

        merger = Merger(schema)

        if return_package:
            packager.package['uri'] = uri
            packager.package['publishedDate'] = published_date
            packager.package['version'] = version
            if publisher:
                packager.package['publisher'] = publisher

            yield from packager.output_package(
                merger,
                return_versioned_release=return_versioned_release,
                use_linked_releases=use_linked_releases,
                streaming=streaming,
                convert_exceptions_to_warnings=convert_exceptions_to_warnings,
            )
        else:
            yield from packager.output_releases(
                merger,
                return_versioned_release=return_versioned_release,
                convert_exceptions_to_warnings=convert_exceptions_to_warnings,
            )
