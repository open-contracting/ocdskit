import itertools
import json
from decimal import Decimal
import ijson

from ocdskit.exceptions import UnknownFormatError

try:
    import orjson

    jsonlib = orjson
    USING_ORJSON = True
except ImportError:
    jsonlib = json
    USING_ORJSON = False


# See `grouper` recipe: https://docs.python.org/3.8/library/itertools.html#recipes
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


# https://stackoverflow.com/questions/21663800/python-make-a-list-generator-json-serializable/46841935#46841935
class SerializableGenerator(list):
    def __init__(self, iterable):
        iterator = iter(iterable)
        try:
            # If `iter()` is omitted, then `__iter__` won't exhaust `head`.
            self.head = iter([next(iterator)])
            # Adding an item to the list ensures `__bool__` and `__len__` work.
            self.append(iterator)
        except StopIteration:
            # `__iter__` requires `head` to be set.
            self.head = []

    def __iter__(self):
        # `*self[:1]` is used, because `self[0]` raises IndexError when `iterable` is empty.
        return itertools.chain(self.head, *self[:1])


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        # https://docs.python.org/3/library/json.html#json.JSONEncoder.default
        try:
            iter(obj)
        except TypeError:
            pass
        else:
            return SerializableGenerator(obj)
        return json.JSONEncoder.default(self, obj)


def iterencode(data, ensure_ascii=False, **kwargs):
    """
    Returns a generator that yields each string representation as available.
    """
    if 'indent' not in kwargs:
        kwargs['separators'] = (',', ':')
    return JSONEncoder(ensure_ascii=ensure_ascii, **kwargs).iterencode(data)


def json_dump(data, io, ensure_ascii=False, **kwargs):
    """
    Dumps JSON to a file-like object.
    """
    if 'indent' not in kwargs:
        kwargs['separators'] = (',', ':')
    json.dump(data, io, ensure_ascii=ensure_ascii, cls=JSONEncoder, **kwargs)


def json_dumps(data, ensure_ascii=False, indent=None, sort_keys=False, **kwargs):
    """
    Dumps JSON to a string, and returns it.
    """
    # orjson doesn't support `ensure_ascii` if `True`, `indent` if not `2` or other arguments except for `sort_keys`.
    if not USING_ORJSON or ensure_ascii or indent and indent != 2 or kwargs:
        if not indent:
            kwargs['separators'] = (',', ':')
        return json.dumps(data, cls=JSONEncoder, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys,
                          **kwargs)

    option = 0
    if indent:
        option |= orjson.OPT_INDENT_2
    if sort_keys:
        option |= orjson.OPT_SORT_KEYS

    # orjson dumps to bytes.
    return orjson.dumps(data, default=JSONEncoder().default, option=option).decode()


def get_ocds_minor_version(data):
    """
    Returns the OCDS minor version of the record package, release package, record or release.
    """
    if is_package(data):
        if 'version' in data:
            return data['version']
        return '1.0'
    if is_record(data):
        if any('parties' in release for release in data['releases']):
            return '1.1'
        return '1.0'
    # release
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

    A record package has a required ``records`` field. Its other required fields are shared with release packages.
    """
    return 'records' in data


def is_record(data):
    """
    Returns whether the data is a record.

    A record has required ``releases`` and ``ocid`` fields.
    """
    return 'releases' in data and 'ocid' in data


def is_release_package(data):
    """
    Returns whether the data is a release package.

    A release package has a required ``releases`` field. Its other required fields are shared with record packages.
    To distinguish a release package from a record, we test for the absence of the ``ocid`` field.
    """
    return 'releases' in data and 'ocid' not in data


def is_release(data):
    """
    Returns whether the data is a release (embedded or linked, individual or compiled).
    """
    return 'date' in data


def is_compiled_release(data):
    """
    Returns whether the data is a compiled release (embedded or linked).
    """
    return 'tag' in data and isinstance(data['tag'], list) and 'compiled' in data['tag']


def is_linked_release(data):
    """
    Returns whether the data is a linked release.

    A linked release has required ``url`` and ``date`` fields and an optional ``tag`` field. An embedded release has
    required ``date`` and ``tag`` fields (among others), and it can have a ``url`` field as an additional field.

    To distinguish a linked release from an embedded release, we test for the presence of the required ``url`` field
    and test whether the number of fields is fewer than three.
    """
    return 'url' in data and len(data) <= 3


def _empty_package(uri, publisher, published_date, version):
    if publisher is None:
        publisher = {}

    return {
        'uri': uri,
        'publisher': publisher,
        'publishedDate': published_date,
        'license': None,
        'publicationPolicy': None,
        'version': version,
        'extensions': {},
    }


def detect_format(path, root_path=''):
    """
    Returns the format of OCDS data, and whether the OCDS data is concatenated or in an array.

    If the OCDS data is concatenated or in an array, assumes that all items have the same format as the first item.

    :param str path: the path to a file
    :param str root_path: the path to the OCDS data within the file
    :returns: the format, whether data is concatenated, and whether data is in an array
    :rtype: tuple
    :raises UnknownFormatError: if the format cannot be detected
    """
    with open(path, 'rb') as f:
        events = iter(ijson.parse(f, multiple_values=True))

        while True:
            prefix, event, value = next(events)
            if prefix == root_path:
                break

        if prefix:
            prefix += '.'

        if event == 'start_array':
            prefix += 'item.'
        elif event != 'start_map':
            raise UnknownFormatError('top-level JSON value is a {}'.format(event))

        records_prefix = '{}records'.format(prefix)
        releases_prefix = '{}releases'.format(prefix)
        ocid_prefix = '{}ocid'.format(prefix)
        tag_item_prefix = '{}tag.item'.format(prefix)

        has_records = False
        has_releases = False
        has_ocid = False
        has_tag = False
        is_compiled = False
        is_array = event == 'start_array'

        for prefix, event, value in events:
            if prefix == records_prefix:
                has_records = True
            elif prefix == releases_prefix:
                has_releases = True
            elif prefix == ocid_prefix:
                has_ocid = True
            elif prefix == tag_item_prefix:
                has_tag = True
                if value == 'compiled':
                    is_compiled = True
            if not prefix and event not in ('end_array', 'end_map', 'map_key'):
                return _detect_format_result(True, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled)

        return _detect_format_result(False, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled)


def _detect_format_result(is_concatenated, is_array, has_records, has_releases, has_ocid, has_tag, is_compiled):
    if has_records:
        detected_format = 'record package'
    elif has_releases and has_ocid:
        detected_format = 'record'
    elif has_releases:
        detected_format = 'release package'
    elif is_compiled:
        detected_format = 'compiled release'
    elif has_tag:
        detected_format = 'release'
    elif has_ocid:
        detected_format = 'versioned release'
    else:
        if is_array:
            infix = 'array'
        else:
            infix = 'object'
        raise UnknownFormatError('top-level JSON value is a non-OCDS {}'.format(infix))

    return (detected_format, is_concatenated, is_array)


def _empty_record_package(uri='', publisher=None, published_date='', version=None):
    package = _empty_package(uri, publisher, published_date, version)
    package['packages'] = []
    package['records'] = []
    return package


def _empty_release_package(uri='', publisher=None, published_date='', version=None):
    package = _empty_package(uri, publisher, published_date, version)
    package['releases'] = []
    return package


def _update_package_metadata(output, package):
    for field in ('publisher', 'license', 'publicationPolicy'):
        if field in package:
            output[field] = package[field]

    # We use an insertion-ordered dict to keep extensions in order without duplication.
    if 'extensions' in package:
        output['extensions'].update(dict.fromkeys(package['extensions']))


def _resolve_metadata(output, field):
    if output[field]:
        output[field] = list(output[field])
    else:
        del output[field]


def _remove_empty_optional_metadata(output):
    for field in ('license', 'publicationPolicy', 'version'):
        if output[field] is None:
            del output[field]
