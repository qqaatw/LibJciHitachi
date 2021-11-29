import pytest

from JciHitachi.api import JciHitachiAPI
from JciHitachi.connection import JciHitachiConnection

from . import api, TEST_EMAIL, TEST_PASSWORD, TEST_DEVICE_AC


class TestLogin:
    def test_api(self, api):
        assert len(api._session_token) == 31
        assert api._peripherals[TEST_DEVICE_AC].name == TEST_DEVICE_AC

    def test_version(self):
        connection = JciHitachiConnection(TEST_EMAIL, TEST_PASSWORD)
        assert connection._login_response["results"]["LatestVersion"]["UpdateSuggestion"] == 0

    def test_session_expiry(self, api):
        invalid_token = "0000000000000000000000000000000"
        api._session_token = invalid_token
        api.refresh_status()

        assert len(api._session_token) == 31
        assert api._session_token != invalid_token

    @pytest.mark.parametrize("mock_device_name", ["NON_EXISTING_NAME"])
    def test_device_name(self, mock_device_name):
        api = JciHitachiAPI(
            TEST_EMAIL,
            TEST_PASSWORD,
            mock_device_name)
        
        with pytest.raises(AssertionError):
            api.login()

    def test_incorrect_credential(self):
        api = JciHitachiAPI("abc@abc.com", "password")
        
        with pytest.raises(RuntimeError):
            api.login()
