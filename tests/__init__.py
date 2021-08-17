import os

import pytest

from JciHitachi.api import JciHitachiAPI

TEST_EMAIL = os.environ['TEST_EMAIL']
TEST_PASSWORD = os.environ['TEST_PASSWORD']
TEST_DEVICE = os.environ['TEST_DEVICE']
MOCK_CODE = os.environ["MOCK_CODE"]
TEST_COMMAND = 'sound_prompt'

MOCK_GATEWAY_MAC = '10416149025290813292'


@pytest.fixture(scope="session")
def api():
    api = JciHitachiAPI(
        TEST_EMAIL,
        TEST_PASSWORD,
        TEST_DEVICE)
    api.login()
    return api
