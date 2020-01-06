import json

import pytest
from ocdsextensionregistry import ProfileBuilder

from ocdskit.combine import compile_release_packages, merge, package_records
from tests import read


def test_package_default_arguments():
    data = [item for filename in ('realdata/record-package-1.json', 'realdata/record-package-2.json')
            for item in json.loads(read(filename))['records']]

    actual = package_records(data)

    assert actual == json.loads(read('realdata/record-package_record-package.json'))


@pytest.mark.vcr()
def test_merge_empty():
    compiled_releases = list(merge([]))

    assert compiled_releases == []


@pytest.mark.vcr()
def test_merge_with_schema():
    builder = ProfileBuilder('1__1__4', {'additionalContactPoint': 'master'})
    schema = builder.patched_release_schema()

    data = json.loads(read('release-package_additional-contact-points.json'))['releases']
    compiled_release = list(merge(data, schema=schema))[0]

    assert compiled_release == json.loads(read('compile_extensions.json'))


@pytest.mark.vcr()
def test_merge_without_schema():
    data = json.loads(read('release-package_additional-contact-points.json'))['releases']
    compiled_release = list(merge(data))[0]

    assert compiled_release == json.loads(read('compile_no-extensions.json'))


@pytest.mark.vcr()
def test_compile_release_packages():
    with pytest.warns(DeprecationWarning) as records:
        compiled_releases = list(compile_release_packages([]))

    assert compiled_releases == []
    assert len(records) == 1
    assert str(records[0].message) == 'compile_release_packages() is deprecated. Use merge() instead.'
