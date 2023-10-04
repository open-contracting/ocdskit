import pytest

import ocdskit.packager


@pytest.fixture(params=[True, False])
def sqlite(request, monkeypatch):
    ocdskit.packager.USING_SQLITE = request.param
