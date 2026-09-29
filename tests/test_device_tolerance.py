"""Per-device failure tolerance: one device answering garbage must not take the others down."""

import logging
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from JciHitachi.api import AWSThing, JciHitachiAWSAPI
from JciHitachi.aws_connection import (
    AWSTokens,
    JciHitachiAuthError,
    JciHitachiAWSMqttConnection,
)
from JciHitachi.model import JciHitachiAWSStatusSupport

IDENTITY = "ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa"
GW_A = "10416149025290813292"
GW_B = "10416149025290813293"


def _thing(name, gw):
    return AWSThing(
        {"DeviceType": "1", "ThingName": f"{IDENTITY}_{gw}", "CustomDeviceName": name}
    )


@pytest.fixture()
def mqtt():
    return JciHitachiAWSMqttConnection(lambda: None)


@pytest.fixture()
def api():
    api = JciHitachiAWSAPI("", "", None)
    api._things = {
        "Device A": _thing("Device A", GW_A),
        "Device B": _thing("Device B", GW_B),
    }
    api._aws_identity = MagicMock(host_identity_id=IDENTITY)
    # valid-looking tokens so _check_before_publish() never tries to reauthenticate for real
    api._aws_tokens = AWSTokens("", "", "", expiration=time.time() + 3600)
    return api


class TestShadowWithoutClientToken:
    def test_cloud_initiated_update_is_ignored_quietly(self, mqtt, caplog):
        response = MagicMock()
        response.client_token = None
        response.state.reported = {
            "online": False,
            "disconnectReason": "CLIENT_INITIATED_DISCONNECT",
        }
        with caplog.at_level(logging.DEBUG):
            mqtt._on_update_named_shadow_accepted(response)
            mqtt._on_get_named_shadow_accepted(response)
        assert "unknown shadow response" not in caplog.text
        assert mqtt._mqtt_events.device_control == {}


class TestShadowAnswerFromAnotherClient:
    """Observed 2026-09-16 16:57 and 2026-09-17 02:34: another client of the same account read
    three shadows and this client received the answers with valid gateway tokens."""

    def _response(self, token):
        response = MagicMock()
        response.client_token = token
        response.state.reported = {"online": True}
        return response

    def test_known_device_token_not_pending_is_debug(self, mqtt, caplog):
        thing = f"{IDENTITY}_{GW_A}"
        mqtt._mqtt_events.device_shadow_event[thing] = (
            threading.Event()
        )  # we asked before
        with caplog.at_level(logging.DEBUG):
            mqtt._on_get_named_shadow_accepted(self._response(GW_A))
            mqtt._on_update_named_shadow_accepted(self._response(GW_A))
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert "another client of the same account" in caplog.text
        assert thing not in mqtt._mqtt_events.device_shadow
        assert not mqtt._mqtt_events.device_shadow_event[thing].is_set()

    def test_token_of_no_known_device_is_error(self, mqtt, caplog):
        with caplog.at_level(logging.DEBUG):
            mqtt._on_get_named_shadow_accepted(self._response("not-a-gateway-id"))
        assert [r for r in caplog.records if r.levelno >= logging.ERROR]

    def test_pending_token_is_still_matched(self, mqtt):
        thing = f"{IDENTITY}_{GW_A}"
        mqtt._client_tokens = {GW_A: thing}
        mqtt._mqtt_events.device_shadow_event[thing] = threading.Event()
        mqtt._on_get_named_shadow_accepted(self._response(GW_A))
        assert mqtt._mqtt_events.device_shadow[thing] == {"online": True}
        assert mqtt._mqtt_events.device_shadow_event[thing].is_set()


class TestThingWithoutSupportCode:
    def test_properties_are_none_safe(self):
        thing = _thing("Device A", GW_A)
        assert thing.brand is None
        assert thing.model is None
        assert thing.firmware_version is None
        assert thing.firmware_code is None

    def test_corrupted_model_string_is_reported_as_unknown(self):
        # observed 2026-09-16 in a registration/response: "Model": "RAD-\xff\x06\x01R"
        thing = _thing("Device A", GW_A)
        thing.support_code = JciHitachiAWSStatusSupport(
            {
                "DeviceType": 1,
                "Model": "RAD-\ufffd\x06\x01R",
                "FirmwareVersion": "6.0.032",
            }
        )
        assert thing.model is None
        assert thing.firmware_version == "6.0.032"
        thing.support_code = JciHitachiAWSStatusSupport(
            {"DeviceType": 1, "Model": "RAD-90NF"}
        )
        assert thing.model == "RAD-90NF"


class TestCognitoErrorClassification:
    def test_only_credential_errors_are_auth_errors(self):
        from JciHitachi.aws_connection import cognito_error

        assert isinstance(
            cognito_error(
                "NotAuthorizedException Incorrect username or password.", "x"
            ),
            JciHitachiAuthError,
        )
        for code in (
            "UserNotFoundException User does not exist.",
            "UserNotConfirmedException User is not confirmed.",
            "PasswordResetRequiredException Password reset required for the user",
        ):
            assert isinstance(cognito_error(code, "x"), JciHitachiAuthError)
        transient = cognito_error("TooManyRequestsException Rate exceeded", "x")
        assert isinstance(transient, RuntimeError)
        assert not isinstance(transient, JciHitachiAuthError)
        assert not isinstance(
            cognito_error("InternalErrorException", "x"), JciHitachiAuthError
        )

    def test_identity_failure_is_an_auth_error(self, api):
        with (
            patch("JciHitachi.aws_connection.GetUser.__init__", return_value=None),
            patch(
                "JciHitachi.aws_connection.GetUser.aws_tokens",
                new_callable=lambda: property(lambda self: MagicMock()),
            ),
            patch(
                "JciHitachi.aws_connection.GetUser.get_data",
                return_value=("NotAuthorizedException", None),
            ),
        ):
            with pytest.raises(JciHitachiAuthError):
                api.login()
