from collections import defaultdict, OrderedDict

from ocdsmerge.merge import merge, merge_versioned, get_tags, get_release_schema_url

from ocdskit.exceptions import InconsistentVersionError
from ocdskit.util import json_loads, get_ocds_minor_version


def combine_record_packages(stream, uri='', publisher=None, published_date=''):
    """
    Reads record packages from the stream, collects packages and records, and returns one record package.
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

    for line in stream:
        package = json_loads(line)

        _update_package_metadata(output, package)

        output['records'].extend(package['records'])

        if 'packages' in package:
            output['packages'].extend(package['packages'])

    if not output['packages']:
        del output['packages']

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def combine_release_packages(stream, uri='', publisher=None, published_date=''):
    """
    Reads release packages from the stream, collects releases, and returns one release package.
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

    for line in stream:
        package = json_loads(line)

        _update_package_metadata(output, package)

        output['releases'].extend(package['releases'])

    _set_extensions_metadata(output)
    _remove_empty_optional_metadata(output)

    return output


def compile_release_packages(stream, uri='', publisher=None, published_date='', schema=None, return_package=False,
                             use_linked_releases=False, add_versioned_release=False):
    """
    Reads release packages from the stream, merges the releases by OCID, and yields the compiled releases.
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

    version = None
    releases_by_ocid = defaultdict(list)
    linked_releases = []

    for i, line in enumerate(stream):
        package = json_loads(line)

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
            _update_package_metadata(output, package)

            output['packages'].append(package['uri'])

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

            if add_versioned_release:
                record['versionedRelease'] = merge_versioned(releases, schema)

            output['records'].append(record)

        _set_extensions_metadata(output)
        _remove_empty_optional_metadata(output)

        yield output
    else:
        for releases in releases_by_ocid.values():
            if add_versioned_release:
                merge_method = merge_versioned
            else:
                merge_method = merge

            merged_release = merge_method(releases, schema)

            yield merged_release


def _update_package_metadata(output, package):
    if 'publisher' in package:
        output['publisher'] = package['publisher']

    if 'extensions' in package:
        # Python has no OrderedSet, so we use OrderedDict to keep extensions in order without duplication.
        output['extensions'].update(OrderedDict.fromkeys(package['extensions']))

    for field in ('license', 'publicationPolicy', 'version'):
        if field in package:
            output[field] = package[field]


def _set_extensions_metadata(output):
    if output['extensions']:
        output['extensions'] = list(output['extensions'])
    else:
        del output['extensions']


def _remove_empty_optional_metadata(output):
    for field in ('license', 'publicationPolicy', 'version'):
        if output[field] is None:
            del output[field]
