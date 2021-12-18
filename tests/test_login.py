import pytest

from JciHitachi.api import JciHitachiAPI
from JciHitachi.connection import JciHitachiConnection
from JciHitachi.mqtt_connection import JciHitachiMqttConnection

from . import fixture_api, fixture_mqtt, TEST_EMAIL, TEST_PASSWORD, TEST_DEVICE_AC


class TestAPILogin:
    def test_api(self, fixture_api):
        assert len(fixture_api._session_token) == 31
        assert fixture_api._peripherals[TEST_DEVICE_AC].name == TEST_DEVICE_AC

    def test_version(self):
        connection = JciHitachiConnection(TEST_EMAIL, TEST_PASSWORD)
        assert connection._login_response["results"]["LatestVersion"]["UpdateSuggestion"] == 0

    def test_session_expiry(self, fixture_api):
        invalid_token = "0000000000000000000000000000000"
        fixture_api._session_token = invalid_token
        fixture_api.refresh_status()

        assert len(fixture_api._session_token) == 31
        assert fixture_api._session_token != invalid_token

    @pytest.mark.parametrize("mock_device_name", ["NON_EXISTING_NAME"])
    def test_device_name(self, mock_device_name):
        api = JciHitachiAPI(
            TEST_EMAIL,
            TEST_PASSWORD,
            mock_device_name)
        
        with pytest.raises(AssertionError, match=r"Some of device_names are not available from the API."):
            api.login()

    def test_incorrect_credential(self):
        api = JciHitachiAPI("abc@abc.com", "password")
        
        with pytest.raises(RuntimeError, match=r"An error occurred when API login:"):
            api.login()


class TestMqttLogin:
    def test_mqtt(self, fixture_mqtt):
        fixture_mqtt.configure()
        fixture_mqtt.connect()
        fixture_mqtt.disconnect()
    
    def test_incorrect_credential(self, fixture_mqtt):
        fixture_mqtt._password = "password"
        fixture_mqtt.configure()
        fixture_mqtt.connect()