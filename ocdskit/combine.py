from ocdsextensionregistry import ProfileBuilder
from ocdsmerge import Merger
from ocdsmerge.util import get_release_schema_url, get_tags

from ocdskit.packager import Packager
from ocdskit.util import (_empty_record_package, _empty_release_package, _remove_empty_optional_metadata,
                          _set_extensions_metadata, _update_package_metadata)


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
        'version': '1.1',  # fields might be deprecated
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

    :param packages: an iterable of record packages
    :param str uri: the record package's ``uri``
    :param dict publisher: the record package's ``publisher``
    :param str published_date: the record package's ``publishedDate``
    """
    # We can postpone the aggregation of records by putting the for-loop in a function that yields each package's
    # records instead of extending the output's records:
    #
    #     output['records'] = itertools.chain.from_iterable(func())
    #
    # This works with simple inputs like:
    #
    #     python -c 'import json; print("\n".join(json.dumps({"records": list(range(1000))}) for x in range(10000)))' |
    #     ocdskit combine-record-packages > /dev/null
    #
    # However, this loop also serves to deduplicate packages and extensions. (It also has logic to replace package
    # metadata, but we can change the logic to use the first package's metadata.)
    #
    # One way to postpone the evaluation of packages, extensions and records is to collect the packages and extensions
    # in a first read of the input, while streaming the records into SQLite – and then streaming them out of SQLite.
    # This effectively reads the inputs twice.
    #
    # Another way is to deduplicate the packages and extensions while yielding the records to a JSON writer that won't
    # yield a closing "}" until the packages and extensions are written. This moves packages and extensions to the end.
    # However, this would require copying and patching the long `_make_iterencode` function from the json module.
    #
    # For now, we are assuming that users aren't attempting to combine so many small packages that they exhaust memory.
    #
    # https://github.com/python/cpython/blob/v3.8.1/Lib/json/encoder.py#L259
    output = _empty_record_package(uri, publisher, published_date)

    for package in packages:
        _update_package_metadata(output, package)
        output['records'].extend(package['records'])

        if 'packages' in package:
            output['packages'].extend(package['packages'])

    if not output['packages']:
        del output['packages']

    if publisher:
        output['publisher'] = publisher

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def combine_release_packages(packages, uri='', publisher=None, published_date=''):
    """
    Collects the releases from the release packages into one release package.

    :param packages: an iterable of release packages
    :param str uri: the release package's ``uri``
    :param dict publisher: the release package's ``publisher``
    :param str published_date: the release package's ``publishedDate``
    """
    # See comment in combine_record_packages regarding streaming.
    output = _empty_release_package(uri, publisher, published_date)

    for package in packages:
        _update_package_metadata(output, package)
        output['releases'].extend(package['releases'])

    if publisher:
        output['publisher'] = publisher

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def merge(data, uri='', publisher=None, published_date='', schema=None, return_versioned_release=False,
          return_package=False, use_linked_releases=False):
    """
    Merges release packages and individual releases.

    By default, yields compiled releases. If ``return_versioned_release`` is ``True``, yields versioned releases. If
    ``return_package`` is ``True``, wraps the compiled releases (and versioned releases if ``return_versioned_release``
    is ``True``) in a record package.

    If ``return_package`` is set and ``publisher`` isn't set, the output record package will have the same publisher as
    the last input release package.

    :param data: an iterable of release packages and individual releases
    :param str uri: if ``return_package`` is ``True``, the record package's ``uri``
    :param dict publisher: if ``return_package`` is ``True``, the record package's ``publisher``
    :param str published_date: if ``return_package`` is ``True``, the record package's ``publishedDate``
    :param dict schema: the URL, path or dict of the patched release schema to use
    :param bool return_package: wrap the compiled releases in a record package
    :param bool use_linked_releases: if ``return_package`` is ``True``, use linked releases instead of full releases,
        if the input is a release package
    :param bool return_versioned_release: if ``return_package`` is ``True``, include versioned releases in the record
        package; otherwise, yield versioned releases instead of compiled releases
    """
    with Packager() as packager:
        packager.add(data)

        if not schema and packager.version:
            prefix = packager.version.replace('.', '__') + '__'
            tag = next(tag for tag in reversed(get_tags()) if tag.startswith(prefix))
            schema = get_release_schema_url(tag)

            if packager.package['extensions']:
                builder = ProfileBuilder(tag, list(packager.package['extensions']))
                schema = builder.patched_release_schema()

        merger = Merger(schema)

        if return_package:
            packager.package['uri'] = uri
            packager.package['publishedDate'] = published_date
            if publisher:
                packager.package['publisher'] = publisher

            yield from packager.output_package(merger, return_versioned_release=return_versioned_release,
                                               use_linked_releases=use_linked_releases)
        else:
            yield from packager.output_releases(merger, return_versioned_release=return_versioned_release)
