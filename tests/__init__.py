import os

import pytest

from JciHitachi.api import JciHitachiAPI
from JciHitachi.mqtt_connection import JciHitachiMqttConnection

TEST_EMAIL = os.environ['TEST_EMAIL']
TEST_PASSWORD = os.environ['TEST_PASSWORD']
MOCK_GATEWAY_MAC = '10416149025290813292'
# AC
TEST_DEVICE_AC = os.environ['TEST_DEVICE_AC']
TEST_COMMAND_AC = 'sound_prompt'
MOCK_CODE_AC = os.environ["MOCK_CODE_AC"]
MOCK_SUPPORT_CODE_AC = os.environ["MOCK_SUPPORT_CODE_AC"]
# DH
TEST_DEVICE_DH = os.environ['TEST_DEVICE_DH']
TEST_COMMAND_DH = 'sound_control'
MOCK_CODE_DH = os.environ["MOCK_CODE_DH"]
MOCK_SUPPORT_CODE_DH = os.environ["MOCK_SUPPORT_CODE_DH"]

@pytest.fixture(scope="session")
def fixture_api():
    api = JciHitachiAPI(
        TEST_EMAIL,
        TEST_PASSWORD,
    )
    api.login()
    return api

@pytest.fixture(scope="function")
def fixture_mqtt(fixture_api):
    mqtt = JciHitachiMqttConnection(
        TEST_EMAIL,
        TEST_PASSWORD,
        fixture_api.user_id, 
    )
    return mqtt