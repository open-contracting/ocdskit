import json

import pytest
from ocdsextensionregistry import ProfileBuilder
from ocdsmerge.exceptions import DuplicateIdValueWarning, InconsistentTypeError

from ocdskit.combine import compile_release_packages, merge, package_records
from ocdskit.exceptions import InconsistentVersionError, MergeErrorWarning, UnknownVersionError
from tests import read

inconsistent = [{
    "ocid": "ocds-213czf-1",
    "date": "2000-01-01T00:00:00Z",
    "integer": 1
}, {
    "ocid": "ocds-213czf-1",
    "date": "2000-01-02T00:00:00Z",
    "integer": {
        "object": 1
    }
}]


def test_package_default_arguments():
    data = [item for filename in ('realdata/record-package-1.json', 'realdata/record-package-2.json')
            for item in json.loads(read(filename))['records']]

    actual = package_records(data)

    assert actual == json.loads(read('realdata/record-package_record-package.json'))


def test_merge_empty():
    compiled_releases = list(merge([]))

    assert compiled_releases == []


def test_merge_with_schema():
    builder = ProfileBuilder('1__1__4', {'additionalContactPoint': 'master'})
    schema = builder.patched_release_schema()

    data = json.loads(read('release-package_additional-contact-points.json'))['releases']
    compiled_release = list(merge(data, schema=schema))[0]

    assert compiled_release == json.loads(read('compile_extensions.json'))


def test_merge_without_schema():
    data = json.loads(read('release-package_additional-contact-points.json'))['releases']
    compiled_release = list(merge(data))[0]

    assert compiled_release == json.loads(read('compile_no-extensions.json'))


def test_merge_warning():
    data = json.loads(read('release-package_warning.json'))['releases']

    with pytest.warns(DuplicateIdValueWarning) as records:
        compiled_release = list(merge(data))[0]

    assert compiled_release == json.loads(read('compile_warning.json'))

    assert [record.message for record in records] == [
        ("ocds-213czf-1: Multiple objects have the `id` value '1' in the `parties` array"),
    ]


def test_merge_unknown_version(capsys, monkeypatch, caplog):
    def data():
        yield json.loads(read('release-package_unknown-version.json'))

    with pytest.raises(UnknownVersionError):
        list(merge(data()))


def test_merge_unknown_version_force_version(capsys, monkeypatch, caplog):
    def data():
        yield json.loads(read('release-package_unknown-version.json'))

    list(merge(data(), force_version='1.1', ignore_version=True))  # no error


def test_merge_version_mismatch():
    def data():
        yield json.loads(read('realdata/release-package_1.1-1.json'))
        yield json.loads(read('realdata/release-package_1.0-1.json'))

    with pytest.raises(InconsistentVersionError):
        list(merge(data()))


def test_merge_version_mismatch_ignore_version():
    def data():
        yield json.loads(read('realdata/release-package_1.1-1.json'))
        yield json.loads(read('realdata/release-package_1.0-1.json'))

    list(merge(data(), ignore_version=True))  # no error


@pytest.mark.parametrize('return_package', [True, False])
def test_merge_inconsistent_type(return_package):
    def data():
        for release in inconsistent:
            yield {'releases': [release]}

    with pytest.raises(InconsistentTypeError):
        list(merge(data(), return_package=return_package))


@pytest.mark.parametrize('return_package,expected', [
    (
        True,
        [
            {
                'uri': '',
                'publisher': {},
                'publishedDate': '',
                'version': '1.1',
                'records': [{'ocid': 'ocds-213czf-1', 'releases': inconsistent}],
            },
        ],
    ),
    (
        False,
        [],
    ),
])
def test_merge_inconsistent_type_convert_exceptions_to_warnings(return_package, expected):
    def data():
        for release in inconsistent:
            yield {'releases': [release]}

    with pytest.warns(MergeErrorWarning) as records:
        output = list(merge(data(), return_package=return_package, convert_exceptions_to_warnings=True))

    assert output == expected
    assert len(records) == 1
    assert str(records[0].message) == "ocds-213czf-1: An earlier release had the literal 1 for /integer, but the current release has an object with a 'object' key"  # noqa: E501


def test_compile_release_packages():
    with pytest.warns(DeprecationWarning) as records:
        compiled_releases = list(compile_release_packages([]))

    assert compiled_releases == []
    assert len(records) == 1
    assert str(records[0].message) == 'compile_release_packages() is deprecated. Use merge() instead.'
