import json
from decimal import Decimal
from types import GeneratorType


def _default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, GeneratorType):
        return list(obj)
    raise TypeError('%s is not JSON serializable' % repr(obj))


def json_dump(data, io, ensure_ascii=False, **kwargs):
    """
    Dumps JSON to a file-like object.
    """
    if 'indent' not in kwargs:
        kwargs['separators'] = (',', ':')

    json.dump(data, io, ensure_ascii=ensure_ascii, default=_default, **kwargs)


def json_dumps(data, ensure_ascii=False, **kwargs):
    """
    Dumps JSON to a string, and returns it.
    """
    if 'indent' not in kwargs:
        kwargs['separators'] = (',', ':')

    return json.dumps(data, ensure_ascii=ensure_ascii, default=_default, **kwargs)


def get_ocds_minor_version(data):
    """
    Returns the OCDS minor version of the release package, record package or release.
    """
    if is_package(data):
        if 'version' in data:
            return data['version']
        return '1.0'
    else:  # release
        if 'parties' in data:
            return '1.1'
        return '1.0'


def is_package(data):
    """
    Returns whether the data is a record package or release package.
    """
    return is_record_package(data) or is_release_package(data)


def is_record_package(data):
    """
    Returns whether the data is a record package.
    """
    return 'records' in data


def is_record(data):
    """
    Returns whether the data is a record.
    """
    return 'releases' in data and 'ocid' in data


def is_release_package(data):
    """
    Returns whether the data is a release package.
    """
    return 'releases' in data and 'ocid' not in data


def is_release(data):
    """
    Returns whether the data is a release.
    """
    return 'tag' in data


def _empty_package(uri, publisher, published_date):
    if publisher is None:
        publisher = {}

    return {
        'uri': uri,
        'publisher': publisher,
        'publishedDate': published_date,
        'license': None,
        'publicationPolicy': None,
        'version': None,
        'extensions': {},
    }


def _empty_record_package(uri='', publisher=None, published_date=''):
    package = _empty_package(uri, publisher, published_date)
    package['packages'] = []
    package['records'] = []
    return package


def _empty_release_package(uri='', publisher=None, published_date=''):
    package = _empty_package(uri, publisher, published_date)
    package['releases'] = []
    return package


def _update_package_metadata(output, package):
    for field in ('publisher', 'license', 'publicationPolicy', 'version'):
        if field in package:
            output[field] = package[field]

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
