import time
import warnings

import pytest
from unittest.mock import patch, MagicMock

from JciHitachi.api import JciHitachiAPI, JciHitachiAWSAPI
from JciHitachi.connection import JciHitachiConnection
from JciHitachi.model import JciHitachiStatus, JciHitachiAWSStatus

from . import fixture_api, fixture_aws_api, fixture_mqtt, TEST_EMAIL, TEST_PASSWORD, TEST_DEVICE_AC


class TestAPILogin:
    def test_api(self, fixture_api):
        assert len(fixture_api._session_token) == 31
        # No peripheral available as we have switched to the new API.
        #assert fixture_api._peripherals[TEST_DEVICE_AC].name == TEST_DEVICE_AC

    def test_version(self):
        connection = JciHitachiConnection(TEST_EMAIL, TEST_PASSWORD)
        assert connection._login_response["results"]["LatestVersion"]["UpdateSuggestion"] == 0

    def test_session_expiry(self, fixture_api):
        invalid_token = "0000000000000000000000000000000"
        fixture_api._session_token = invalid_token
        fixture_api.login()

        assert len(fixture_api._session_token) == 31
        assert fixture_api._session_token != invalid_token
    
    def test_deprecated_warning(self):
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            # Trigger a warning.
            api = JciHitachiAPI(TEST_EMAIL, TEST_PASSWORD)
            # Verify some things
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "This API has been deprecated." in str(w[-1].message)

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


class TestAWSAPILogin:
    def test_api(self, fixture_aws_api):
        assert fixture_aws_api._aws_tokens is not None
        assert fixture_aws_api._aws_identity is not None
        assert fixture_aws_api._aws_credentials is not None
        assert fixture_aws_api.things[TEST_DEVICE_AC].name == TEST_DEVICE_AC

    def test_session_expiry(self, fixture_aws_api):
        # Test AWSTokens expiration
        current_access_token = fixture_aws_api._aws_tokens.access_token
        current_session_token = fixture_aws_api._aws_credentials.session_token
        expiration = time.time() + 150.0
        fixture_aws_api._aws_tokens.expiration = expiration
        fixture_aws_api.refresh_status()
        assert fixture_aws_api._aws_tokens.access_token != current_access_token
        assert fixture_aws_api._aws_credentials.session_token != current_session_token
        assert fixture_aws_api._aws_tokens.expiration != expiration
        
        # Test AWSCredentials expiration
        current_access_token = fixture_aws_api._aws_tokens.access_token
        current_session_token = fixture_aws_api._aws_credentials.session_token
        expiration = time.time() + 150.0
        fixture_aws_api._aws_credentials.expiration = expiration
        fixture_aws_api.refresh_status()
        assert fixture_aws_api._aws_tokens.access_token != current_access_token
        assert fixture_aws_api._aws_credentials.session_token != current_session_token
        assert fixture_aws_api._aws_credentials.expiration != expiration

    @pytest.mark.parametrize("mock_device_name", ["NON_EXISTING_NAME"])
    def test_device_name(self, mock_device_name):
        api = JciHitachiAWSAPI(
            TEST_EMAIL,
            TEST_PASSWORD,
            mock_device_name)
        
        with pytest.raises(AssertionError, match=r"Some of device_names are not available from the API."):
            api.login()

    def test_incorrect_credential(self):
        api = JciHitachiAWSAPI("abc@abc.com", "password")
        
        with pytest.raises(RuntimeError, match=r"An error occurred when signing into AWS Cognito Service:"):
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


class TestAWSAPI:
    def test_get_status(self, fixture_aws_api):
        # Test AWS status
        statuses = fixture_aws_api.get_status(TEST_DEVICE_AC)
        assert isinstance(statuses[TEST_DEVICE_AC], JciHitachiAWSStatus)
        # Test legacy status
        statuses = fixture_aws_api.get_status(TEST_DEVICE_AC, True)
        assert isinstance(statuses[TEST_DEVICE_AC], JciHitachiStatus)
        # Test not existing thing
        statuses = fixture_aws_api.get_status("NON_EXISTING_NAME")
        assert statuses == {}

    def test_refresh_status(self, fixture_aws_api):
        return
        api = JciHitachiAWSAPI("", "")
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_publish = MagicMock()
            mock_publish.return_value = None
            mock_publish.side_effect = lambda *args: api._mqtt.mqtt_events.device_status_event.set()
            mock_mqtt.publish = mock_publish
            api.refresh_status(TEST_DEVICE_AC)

            mock_publish.side_effect = None
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {TEST_DEVICE_AC} status code."):
                api.refresh_status(TEST_DEVICE_AC)

        with patch.object(api._mqtt, "publish") as mock_publish:
            mock_publish.return_value = None
            mock_publish.side_effect = lambda *args: api._mqtt.mqtt_events.device_support_event.set()
            api.refresh_status(TEST_DEVICE_AC, refresh_support_code=True)
            
            mock_publish.side_effect = None
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {TEST_DEVICE_AC} support code."):
                api.refresh_status(TEST_DEVICE_AC, refresh_support_code=True)
        
        with patch.object(fixture_aws_api._mqtt, "publish") as mock_publish:
            mock_publish.return_value = None
            mock_publish.side_effect = fixture_aws_api._mqtt.mqtt_events.device_status_event.set

            with patch.object(fixture_aws_api._mqtt, "publish_shadow") as mock_publish_shadow:
                mock_publish_shadow.return_value = None
                mock_publish_shadow.side_effect = lambda *args: fixture_aws_api._mqtt.mqtt_events.device_shadow_event.set
                fixture_aws_api.refresh_status(TEST_DEVICE_AC, refresh_shadow=True)

                mock_publish_shadow.side_effect = None
                with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {TEST_DEVICE_AC} shadow."):
                    fixture_aws_api.refresh_status(TEST_DEVICE_AC, refresh_shadow=True)


    def test_set_status(self):
        return
    
    def test_get_monthly_data(self):
        return