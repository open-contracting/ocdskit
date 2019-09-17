from collections import defaultdict, OrderedDict

from ocdsextensionregistry import ProfileBuilder
from ocdsmerge.merge import merge, merge_versioned, get_tags, get_release_schema_url

from ocdskit.exceptions import InconsistentVersionError
from ocdskit.util import get_ocds_minor_version


def package_releases(releases, uri='', publisher=None, published_date='', extensions=None):
    """
    Wraps releases in a release package.

    :param list releases: a list of releases
    :param str uri: the release package's ``uri``
    :param dict publisher: the release package's ``publisher``
    :param str published_date: the release package's ``publishedDate``
    :param list extensions: the release package's ``extensions``
    """
    if publisher is None:
        publisher = OrderedDict()
    if extensions is None:
        extensions = []

    output = OrderedDict([
        ('uri', uri),
        ('publisher', publisher),
        ('publishedDate', published_date),
        ('version', '1.1'),
        ('extensions', extensions),
        ('releases', releases),
    ])

    return output


def combine_record_packages(packages, uri='', publisher=None, published_date=''):
    """
    Collects the packages and records from the record packages into one record package.

    :param list packages: a list of record packages
    :param str uri: the record package's ``uri``
    :param dict publisher: the record package's ``publisher``
    :param str published_date: the record package's ``publishedDate``
    """
    if publisher is None:
        publisher = OrderedDict()

    output = OrderedDict([
        ('uri', uri),
        ('publisher', publisher),
        ('publishedDate', published_date),
        ('license', None),
        ('publicationPolicy', None),
        ('version', None),
        ('extensions', OrderedDict()),
        ('packages', []),
        ('records', []),
    ])

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
        publisher = OrderedDict()

    output = OrderedDict([
        ('uri', uri),
        ('publisher', publisher),
        ('publishedDate', published_date),
        ('license', None),
        ('publicationPolicy', None),
        ('version', None),
        ('extensions', OrderedDict()),
        ('releases', []),
    ])

    for package in packages:
        _update_package_metadata(output, package, publisher)

        output['releases'].extend(package['releases'])

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def compile_release_packages(packages, uri='', publisher=None, published_date='', schema=None,
                             return_versioned_release=False, return_package=False, use_linked_releases=False):
    """
    Merges releases by OCID and yields compiled releases.

    If ``return_versioned_release`` is ``True``, yields the versioned release. If ``return_package`` is ``True``, wraps
    the compiled releases (and versioned releases if ``return_versioned_release`` is ``True``) in a record package.

    If ``return_package`` is set and ``publisher`` isn't set, the output record package will have the same publisher as
    the last input release package.

    :param list packages: a list of release packages
    :param str uri: if ``return_package`` is ``True``, the record package's ``uri``
    :param dict publisher: if ``return_package`` is ``True``, the record package's ``publisher``
    :param str published_date: if ``return_package`` is ``True``, the record package's ``publishedDate``
    :param dict schema: the URL or path of the release schema to use
    :param bool return_package: wrap the compiled releases in a record package
    :param bool use_linked_releases: if ``return_package`` is ``True``, use linked releases instead of full releases
    :param bool return_versioned_release: if ``return_package`` is ``True``, include versioned releases in the record
        package; otherwise, yield versioned releases instead of compiled releases
    """
    if return_package:
        output = OrderedDict([
            ('uri', uri),
            ('publisher', publisher),
            ('publishedDate', published_date),
            ('license', None),
            ('publicationPolicy', None),
            ('version', None),
            ('extensions', OrderedDict()),
            ('packages', []),
            ('records', []),
        ])
    # To avoid duplicating code, we track extensions in the same place even if ``return_package`` is false.
    else:
        output = {
            'extensions': OrderedDict(),
        }

    version = None
    releases_by_ocid = defaultdict(list)
    linked_releases = []

    for i, package in enumerate(packages):
        if not version:
            version = get_ocds_minor_version(package)
        else:
            v = get_ocds_minor_version(package)
            if v != version:
                raise InconsistentVersionError('item {}: version error: this package uses version {}, but earlier '
                                               'packages used version {}'.format(i, v, version), version, v)

        if not schema:
            prefix = version.replace('.', '__') + '__'
            tag = next(tag for tag in reversed(get_tags()) if tag.startswith(prefix))
            schema = get_release_schema_url(tag)

        for release in package['releases']:
            releases_by_ocid[release['ocid']].append(release)

            if return_package and use_linked_releases:
                linked_releases.append(OrderedDict([
                    ('url', package['uri'] + '#' + release['id']),
                    ('date', release['date']),
                    ('tag', release['tag']),
                ]))

        if return_package:
            _update_package_metadata(output, package, publisher)

            output['packages'].append(package['uri'])
        else:
            _update_extensions_metadata(output, package)

    if output['extensions']:
        builder = ProfileBuilder(tag, list(output['extensions']))
        schema = builder.patched_release_schema()

    if return_package:
        for ocid, releases in releases_by_ocid.items():
            record = OrderedDict([
                ('ocid', ocid),
                ('releases', []),
                ('compiledRelease', merge(releases, schema)),
            ])

            if use_linked_releases:
                record['releases'] = linked_releases
            else:
                record['releases'] = releases

            if return_versioned_release:
                record['versionedRelease'] = merge_versioned(releases, schema)

            output['records'].append(record)

        _set_extensions_metadata(output)
        _remove_empty_optional_metadata(output)

        yield output
    else:
        for releases in releases_by_ocid.values():
            if return_versioned_release:
                merge_method = merge_versioned
            else:
                merge_method = merge

            merged_release = merge_method(releases, schema)

            yield merged_release


def _update_package_metadata(output, package, publisher):
    _update_extensions_metadata(output, package)

    if not publisher and 'publisher' in package:
        output['publisher'] = package['publisher']

    for field in ('license', 'publicationPolicy', 'version'):
        if field in package:
            output[field] = package[field]


def _update_extensions_metadata(output, package):
    if 'extensions' in package:
        # Python has no OrderedSet, so we use OrderedDict to keep extensions in order without duplication.
        output['extensions'].update(OrderedDict.fromkeys(package['extensions']))


def _set_extensions_metadata(output):
    if output['extensions']:
        output['extensions'] = list(output['extensions'])
    else:
        del output['extensions']


def _remove_empty_optional_metadata(output):
    for field in ('license', 'publicationPolicy', 'version'):
        if output[field] is None:
            del output[field]
