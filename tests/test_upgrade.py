from collections import OrderedDict

import pytest

from ocdskit.upgrade import upgrade_10_11


def test_upgrade_10_11_reorder():
    data = OrderedDict([("releases", [OrderedDict([("ocid", "ocds-1"), ("buyer", OrderedDict([("name", "Acme")]))])])])

    result = upgrade_10_11(data)

    assert list(result) == ["version", "releases"]
    assert list(result["releases"][0]) == ["ocid", "parties", "buyer"]


def test_upgrade_10_11_no_reorder():
    data = {"releases": [{"ocid": "ocds-1", "buyer": {"name": "Acme"}}]}

    result = upgrade_10_11(data, reorder=False)

    assert list(result) == ["releases", "version"]
    assert list(result["releases"][0]) == ["ocid", "buyer", "parties"]


def test_upgrade_10_11_reorder_dict():
    data = {"releases": [{"ocid": "ocds-1", "buyer": {"name": "Acme"}}]}

    with pytest.raises(AttributeError):
        upgrade_10_11(data)
