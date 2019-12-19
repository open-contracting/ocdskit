import json

from ocdskit.upgrade import upgrade_10_11
from tests import read


def test_upgrade():
    package = upgrade_10_11(json.loads(read('realdata/record-package_1.0.json')))

    assert package == json.loads(read('realdata/record-package_1.1.json'))
