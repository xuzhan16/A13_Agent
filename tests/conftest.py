import os

import pytest


INTEGRATION_FILES = {
    'test_resume_structuring.py',
}


def pytest_runtest_setup(item):
    if item.fspath.basename in INTEGRATION_FILES and os.environ.get('RUN_APP_INTEGRATION_TESTS') != '1':
        pytest.skip('App integration tests require a live Neo4j-backed service. Set RUN_APP_INTEGRATION_TESTS=1 to enable them.')
