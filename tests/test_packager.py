import json

import pytest
from ocdsmerge import Merger
from ocdsmerge.util import get_release_schema_url, get_tags

from ocdskit.packager import Packager
from tests import read


@pytest.mark.vcr()
def test_output_package_no_streaming():
    data = [json.loads(read(filename)) for filename in
            ('realdata/release-package-1.json', 'realdata/release-package-2.json')]

    with Packager() as packager:
        packager.package['version'] = '1.1'
        packager.add(data)

        prefix = packager.version.replace('.', '__') + '__'
        tag = next(tag for tag in reversed(get_tags()) if tag.startswith(prefix))
        schema = get_release_schema_url(tag)

        actual = next(packager.output_package(Merger(schema)))

    assert actual == json.loads(read('realdata/record-package_package.json'))
