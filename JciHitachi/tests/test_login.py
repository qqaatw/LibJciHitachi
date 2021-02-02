import os

import pytest

from JciHitachi.api import JciHitachiAPI
from JciHitachi.connection import JciHitachiConnection, APP_VERSION

TEST_EMAIL = os.environ['TEST_EMAIL']
TEST_PASSWORD = os.environ['TEST_PASSWORD']
TEST_DEVICE = os.environ['TEST_DEVICE']


class TestLogin:
    def test_api(self):
        api = JciHitachiAPI(
            TEST_EMAIL,
            TEST_PASSWORD,
            TEST_DEVICE)
        api.login()
        assert len(api._code) == 92

    def test_version(self):
        connection = JciHitachiConnection(TEST_EMAIL, TEST_PASSWORD)
        assert connection._login_response["results"]["LatestVersion"]["UpdateSuggestion"] == 0

    @pytest.mark.parametrize("mock_device_name", ["NON_EXISTING_NAME"])
    def test_device_name(self, mock_device_name):
        with pytest.raises(ValueError):
            api = JciHitachiAPI(
                TEST_EMAIL,
                TEST_PASSWORD,
                mock_device_name)
            api.login()

    @pytest.mark.parametrize("mock_device_type", ["Humidifier", "HeatExchanger"])
    def test_device_type(self, mock_device_type):
        with pytest.raises(AssertionError):
            api = JciHitachiAPI(
                TEST_EMAIL,
                TEST_PASSWORD,
                TEST_DEVICE,
                device_type=mock_device_type)
