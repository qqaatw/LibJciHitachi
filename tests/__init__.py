import os

import pytest

from JciHitachi.api import JciHitachiAPI

TEST_EMAIL = os.environ['TEST_EMAIL']
TEST_PASSWORD = os.environ['TEST_PASSWORD']
# AC
TEST_DEVICE_AC = os.environ['TEST_DEVICE_AC']
TEST_COMMAND_AC = 'sound_prompt'
MOCK_CODE_AC = os.environ["MOCK_CODE_AC"]
# DH
TEST_DEVICE_DH = os.environ['TEST_DEVICE_DH']
TEST_COMMAND_DH = 'sound_control'
MOCK_CODE_DH = os.environ["MOCK_CODE_DH"]


@pytest.fixture(scope="session")
def api():
    api = JciHitachiAPI(
        TEST_EMAIL,
        TEST_PASSWORD,
        TEST_DEVICE_AC)
    api.login()
    return api
