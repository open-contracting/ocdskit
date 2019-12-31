import json

from ocdsextensionregistry import ProfileBuilder

from ocdskit.combine import merge
from tests import read


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
