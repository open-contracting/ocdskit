import json

import pytest
from ocdsextensionregistry import ProfileBuilder
from ocdsmerge.exceptions import DuplicateIdValueWarning

from ocdskit.combine import compile_release_packages, merge, package_records
from ocdskit.exceptions import InconsistentVersionError, UnknownVersionError
from tests import read


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


def test_compile_release_packages():
    with pytest.warns(DeprecationWarning) as records:
        compiled_releases = list(compile_release_packages([]))

    assert compiled_releases == []
    assert len(records) == 1
    assert str(records[0].message) == 'compile_release_packages() is deprecated. Use merge() instead.'
