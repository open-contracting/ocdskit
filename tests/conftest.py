import os.path
import logging

import pytest

logger = logging.getLogger('vcr')
logger.setLevel(logging.WARNING)


@pytest.fixture
def vcr_cassette_name(request):
    return '{}-{}'.format(os.path.splitext(os.path.basename(request.node.fspath))[0], request.node.name)
