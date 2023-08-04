import time
import warnings

import pytest

from JciHitachi.api import JciHitachiAPI, JciHitachiAWSAPI
from JciHitachi.connection import JciHitachiConnection
from JciHitachi.mqtt_connection import JciHitachiMqttConnection
from JciHitachi.status import JciHitachiAC, JciHitachiDH

from . import (
    MOCK_COMMAND_AC,
    MOCK_COMMAND_DH,
    TEST_DEVICE_AC,
    TEST_DEVICE_DH,
    TEST_EMAIL,
    TEST_PASSWORD,
)


pytestmark = pytest.mark.skipif(
    TEST_EMAIL is None, reason="No secrets for integration tests"
)


@pytest.fixture(scope="session")
def fixture_api():
    api = JciHitachiAPI(
        TEST_EMAIL,
        TEST_PASSWORD,
    )
    api.login()
    return api


@pytest.fixture(scope="session")
def fixture_aws_api():
    api = JciHitachiAWSAPI(
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


class TestAPILogin:
    def test_api(self, fixture_api):
        assert len(fixture_api._session_token) == 31
        # No peripheral available as we have switched to the new API.
        # assert fixture_api._peripherals[TEST_DEVICE_AC].name == TEST_DEVICE_AC

    def test_version(self):
        connection = JciHitachiConnection(TEST_EMAIL, TEST_PASSWORD)
        assert (
            connection._login_response["results"]["LatestVersion"]["UpdateSuggestion"]
            == 0
        )

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
        api = JciHitachiAPI(TEST_EMAIL, TEST_PASSWORD, mock_device_name)

        with pytest.raises(
            AssertionError,
            match=r"Some of device_names are not available from the API.",
        ):
            api.login()

    def test_incorrect_credential(self):
        api = JciHitachiAPI("abc@abc.com", "password")

        with pytest.raises(RuntimeError, match=r"An error occurred when API login:"):
            api.login()


class TestAWSAPILogin:
    def test_api(self, fixture_aws_api):
        assert fixture_aws_api._aws_tokens is not None
        assert fixture_aws_api._aws_identity is not None
        assert fixture_aws_api.things[TEST_DEVICE_AC].name == TEST_DEVICE_AC

    def test_session_expiry(self, fixture_aws_api):
        # Test AWSTokens expiration
        current_access_token = fixture_aws_api._aws_tokens.access_token
        expiration = time.time() + 150.0
        fixture_aws_api._aws_tokens.expiration = expiration
        fixture_aws_api.refresh_status()
        assert fixture_aws_api._aws_tokens.access_token != current_access_token
        assert fixture_aws_api._aws_tokens.expiration != expiration

    @pytest.mark.parametrize("mock_device_name", ["NON_EXISTING_NAME"])
    def test_device_name(self, mock_device_name):
        api = JciHitachiAWSAPI(TEST_EMAIL, TEST_PASSWORD, mock_device_name)

        with pytest.raises(
            AssertionError,
            match=r"Some of device_names are not available from the API.",
        ):
            api.login()

    def test_incorrect_credential(self):
        api = JciHitachiAWSAPI("abc@abc.com", "password")

        with pytest.raises(
            RuntimeError,
            match=r"An error occurred when signing into AWS Cognito Service:",
        ):
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


class TestACStatus:
    @pytest.mark.slow("online test is a slow test.")
    def test_online(self, fixture_api):
        # Change sound prompt
        current_state = fixture_api.get_status()[TEST_DEVICE_AC]._status[
            JciHitachiAC.idx[MOCK_COMMAND_AC]
        ]
        if current_state != 1:
            changed_state = 1
        else:
            changed_state = 0
        assert fixture_api.set_status(MOCK_COMMAND_AC, changed_state, TEST_DEVICE_AC)

        fixture_api.refresh_status()
        assert (
            fixture_api.get_status()[TEST_DEVICE_AC]._status[
                JciHitachiAC.idx[MOCK_COMMAND_AC]
            ]
            == changed_state
        )

        # Change sound prompt back
        assert fixture_api.set_status(MOCK_COMMAND_AC, current_state, TEST_DEVICE_AC)

        fixture_api.refresh_status()
        assert (
            fixture_api.get_status()[TEST_DEVICE_AC]._status[
                JciHitachiAC.idx[MOCK_COMMAND_AC]
            ]
            == current_state
        )


class TestDHStatus:
    @pytest.mark.skip("Skip online test as no usable account to test.")
    def test_online(self, fixture_api):
        # Change sound control
        current_state = fixture_api.get_status()[TEST_DEVICE_DH]._status[
            JciHitachiDH.idx[MOCK_COMMAND_DH]
        ]
        if current_state != 1:
            changed_state = 1
        else:
            changed_state = 0
        assert fixture_api.set_status(MOCK_COMMAND_DH, changed_state, TEST_DEVICE_DH)

        fixture_api.refresh_status()
        assert (
            fixture_api.get_status()[TEST_DEVICE_DH]._status[
                JciHitachiDH.idx[MOCK_COMMAND_DH]
            ]
            == changed_state
        )

        # Change Change sound control back
        assert fixture_api.set_status(MOCK_COMMAND_DH, current_state, TEST_DEVICE_DH)

        fixture_api.refresh_status()
        assert (
            fixture_api.get_status()[TEST_DEVICE_DH]._status[
                JciHitachiDH.idx[MOCK_COMMAND_DH]
            ]
            == current_state
        )
