import gzip
import json

import ijson
import pytest

from ocdskit.exceptions import UnknownFormatError
from ocdskit.util import (
    detect_format,
    get_ocds_minor_version,
    is_compiled_release,
    is_linked_release,
    is_package,
    is_record,
    is_record_package,
    is_release,
    is_release_package,
    json_dump,
)
from tests import path, read


# Same fixture files as in test_detect_format.py, except for concatenated JSON files.
@pytest.mark.parametrize(('filename', 'expected'), [
    ('record-package_minimal.json', True),
    ('release-package_minimal.json', True),
    ('record_minimal.json', False),
    ('release_minimal.json', False),
    ('realdata/compiled-release-1.json', False),
    ('realdata/versioned-release-1.json', False),
    ('release-packages.json', False),
    ('detect-format_whitespace.json', False),
])
def test_is_package(filename, expected):
    assert is_package(json.loads(read(filename))) == expected


@pytest.mark.parametrize(('filename', 'expected'), [
    ('record-package_minimal.json', True),
    ('release-package_minimal.json', False),
    ('record_minimal.json', False),
    ('release_minimal.json', False),
    ('realdata/compiled-release-1.json', False),
    ('realdata/versioned-release-1.json', False),
    ('release-packages.json', False),
    ('detect-format_whitespace.json', False),
])
def test_is_record_package(filename, expected):
    assert is_record_package(json.loads(read(filename))) == expected


@pytest.mark.parametrize(('filename', 'expected'), [
    ('record-package_minimal.json', False),
    ('release-package_minimal.json', False),
    ('record_minimal.json', True),
    ('release_minimal.json', False),
    ('realdata/compiled-release-1.json', False),
    ('realdata/versioned-release-1.json', False),
    ('release-packages.json', False),
    ('detect-format_whitespace.json', False),
])
def test_is_record(filename, expected):
    assert is_record(json.loads(read(filename))) == expected


@pytest.mark.parametrize(('filename', 'expected'), [
    ('record-package_minimal.json', False),
    ('release-package_minimal.json', True),
    ('record_minimal.json', False),
    ('release_minimal.json', False),
    ('realdata/compiled-release-1.json', False),
    ('realdata/versioned-release-1.json', False),
    ('release-packages.json', False),
    ('detect-format_whitespace.json', False),
])
def test_is_release_package(filename, expected):
    assert is_release_package(json.loads(read(filename))) == expected


@pytest.mark.parametrize(('filename', 'expected'), [
    ('record-package_minimal.json', False),
    ('release-package_minimal.json', False),
    ('record_minimal.json', False),
    ('release_minimal.json', True),
    ('realdata/compiled-release-1.json', True),
    ('realdata/versioned-release-1.json', False),
    ('release-packages.json', False),
    ('detect-format_whitespace.json', True),
])
def test_is_release(filename, expected):
    assert is_release(json.loads(read(filename))) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z', 'tag': ['compiled']}, True),
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z', 'tag': ['tender']}, False),
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z', 'tag': None}, False),
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z'}, False),
])
def test_is_compiled_release(data, expected):
    assert is_compiled_release(data) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ({'url': 'http://example.com'}, True),
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z'}, True),
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z', 'tag': ['tender']}, True),
    ({'url': 'http://example.com', 'date': '2001-02-03T04:05:06Z', 'tag': ['tender'], 'id': '1'}, False),
])
def test_is_linked_release(data, expected):
    assert is_linked_release(data) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    ({'records': [], 'version': '99.99'}, '99.99'),
    ({'records': []}, '1.0'),
    ({'releases': [], 'version': '99.99'}, '99.99'),
    ({'releases': []}, '1.0'),
    # An additional `version` field is provided on records and releases, to be sure it isn't used.
    ({'version': '99.99', 'ocid': 'ocds-213czf-1', 'releases': [{'parties': []}]}, '1.1'),
    ({'version': '99.99', 'ocid': 'ocds-213czf-1', 'releases': []}, '1.0'),
    ({'version': '99.99', 'ocid': 'ocds-213czf-1', 'parties': []}, '1.1'),
    ({'version': '99.99', 'ocid': 'ocds-213czf-1'}, '1.0'),
])
def test_get_ocds_minor_version(data, expected):
    assert get_ocds_minor_version(data) == expected


@pytest.mark.parametrize(('data', 'expected'), [
    (iter([]), '[]'),
    ({'a': 1, 'b': 2}, '{"a":1,"b":2}'),
])
def test_json_dump(data, expected, tmpdir):
    p = tmpdir.join('test.json')

    with open(p, 'w') as f:
        json_dump(data, f)

    assert p.read() == expected


@pytest.mark.parametrize(('filename', 'expected'), [
    ('record-package_minimal.json', ('record package', False, False)),
    ('release-package_minimal.json', ('release package', False, False)),
    ('record_minimal.json', ('record', False, False)),
    ('release_minimal.json', ('release', False, False)),
    ('realdata/compiled-release-1.json', ('compiled release', False, False)),
    ('realdata/versioned-release-1.json', ('versioned release', False, False)),
    ('release-packages.json', ('release package', False, True)),
    ('release-packages.jsonl', ('release package', True, True)),
    ('detect-format_mixed.json', ('release', True, False)),
    ('detect-format_whitespace.json', ('release', False, False)),
    ('detect-format_empty.json', ('empty package', False, False)),
])
def test_detect_format(filename, expected):
    result = detect_format(path(filename))

    assert result == expected


@pytest.mark.parametrize(('filename', 'expected'), [
    ('ocds-sample-data.json.gz', ('release package', False, False))
])
def test_detect_format_gz(filename, expected):
    result = detect_format(path(filename), reader=gzip.open)

    assert result == expected


@pytest.mark.parametrize(('text', 'is_array'), [
    ('{"publishedDate": "","uri":"","version":"","extensions":[]}', False),
    ('[{"publishedDate": "","uri":"","version":"","extensions":[]}]', True),
    ('{"publishedDate": "","uri":"","version":"","publisher":{"uri":""}}', False),
    ('[{"publishedDate": "","uri":"","version":"","publisher":{"uri":""}}]', True),
])
def test_detect_format_prefixes(text, is_array, tmp_path):
    path = tmp_path / 'test.json'
    path.write_text(text)

    result = detect_format(path, additional_prefixes=('extensions', 'publisher'))

    assert result == ('empty package', False, is_array)


@pytest.mark.parametrize(('text', 'infix'), [
    ('"0"', 'string'),
    ('0', 'number'),
    ('true', 'boolean'),
    ('false', 'boolean'),
    ('null', 'null'),
])
def test_detect_format_incorrect_type(text, infix, tmp_path):
    path = tmp_path / 'test.json'
    path.write_text(text)

    with pytest.raises(UnknownFormatError) as excinfo:
        detect_format(path)

    assert str(excinfo.value) == f'top-level JSON value is a {infix}'


@pytest.mark.parametrize(('text', 'infix'), [
    ('{}', 'object'),
    ('[{}]', 'array'),
])
def test_detect_format_incorrect_keys(text, infix, tmp_path):
    path = tmp_path / 'test.json'
    path.write_text(text)

    with pytest.raises(UnknownFormatError) as excinfo:
        detect_format(path)

    assert str(excinfo.value) == f'top-level JSON value is a non-OCDS {infix}'


def test_detect_format_empty(tmp_path):
    path = tmp_path / 'test.json'
    path.write_text('')

    with pytest.raises(ijson.common.IncompleteJSONError):
        detect_format(path)  # "parse error: premature EOF"
