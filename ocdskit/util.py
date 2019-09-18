import json
from collections import OrderedDict
from decimal import Decimal
from types import GeneratorType


def json_load(io):
    """
    Parses JSON from a file-like object.
    """
    return json.load(io, object_pairs_hook=OrderedDict)


def json_loads(data):
    """
    Parses JSON from a string.
    """
    return json.loads(data, object_pairs_hook=OrderedDict)


def json_dump(data, io, indent=2):
    """
    Dumps JSON to a file-like object.
    """
    json.dump(data, io, ensure_ascii=False, indent=indent, separators=(',', ': '))


def json_dumps(data, **kwargs):
    """
    Dumps JSON to a string, and returns it.
    """
    def default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, GeneratorType):
            return list(obj)
        raise TypeError('%s is not JSON serializable' % repr(obj))

    return json.dumps(data, default=default, **kwargs)


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


def is_release_package(data):
    """
    Returns whether the data is a release package.
    """
    # Disambiguate a release package from a record.
    return 'releases' in data and 'ocid' not in data
