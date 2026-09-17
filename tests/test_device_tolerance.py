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
    JciHitachiDeviceError,
)
from JciHitachi.model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

IDENTITY = "ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa"
GW_A = "10416149025290813292"
GW_B = "10416149025290813293"
BINARY_FRAME = (
    b"\xfc\xff\xff\x1f\x01\x01"  # observed from three RAD-series ACs, 2026-08/09
)


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


class TestOnPublishUndecodable:
    def test_binary_registration_response_is_recorded_and_releases_waiter(
        self, mqtt, caplog
    ):
        thing = f"{IDENTITY}_{GW_A}"
        topic = f"{IDENTITY}/{thing}/registration/response"
        mqtt._mqtt_events.device_support_event[thing] = threading.Event()
        mqtt._mqtt_events.mqtt_error_event.clear()

        with caplog.at_level(logging.DEBUG):
            mqtt._on_publish(topic, BINARY_FRAME, None, None, None)

        assert mqtt._mqtt_events.device_undecodable[thing] == {
            "registration": (topic, BINARY_FRAME)
        }
        assert mqtt._mqtt_events.device_support_event[thing].is_set(), (
            "waiter must not burn the timeout"
        )
        assert thing not in mqtt._mqtt_events.device_support
        assert not mqtt._mqtt_events.mqtt_error_event.is_set(), (
            "a per-device frame must not trigger reauth"
        )
        assert "fcffff1f0101" in caplog.text

    def test_binary_frame_on_unrequested_topic_does_not_raise(self, mqtt):
        thing = f"{IDENTITY}_{GW_A}"
        # `statistic` and `status-secondary` are only requested by the official app
        mqtt._on_publish(
            f"{IDENTITY}/{thing}/statistic/response", BINARY_FRAME, None, None, None
        )
        mqtt._on_publish(
            f"{IDENTITY}/{thing}/status-secondary/response",
            BINARY_FRAME,
            None,
            None,
            None,
        )
        assert set(mqtt._mqtt_events.device_undecodable[thing]) == {
            "statistic",
            "status-secondary",
        }

    def test_undecodable_without_thing_keeps_global_error(self, mqtt):
        mqtt._mqtt_events.mqtt_error_event.clear()
        mqtt._on_publish("", b"", None, None, None)
        assert mqtt._mqtt_events.mqtt_error_event.is_set()

    def test_response_before_publish_created_event_does_not_raise(self, mqtt):
        thing = f"{IDENTITY}_{GW_A}"
        assert thing not in mqtt._mqtt_events.device_status_event
        # previously KeyError inside the awscrt callback thread
        mqtt._on_publish(
            f"{IDENTITY}/{thing}/status/response",
            b'{"DeviceType": 1}',
            None,
            None,
            None,
        )
        assert isinstance(mqtt._mqtt_events.device_status[thing], JciHitachiAWSStatus)

    def test_good_response_clears_earlier_undecodable(self, mqtt):
        thing = f"{IDENTITY}_{GW_A}"
        mqtt._on_publish(
            f"{IDENTITY}/{thing}/status/response", BINARY_FRAME, None, None, None
        )
        mqtt._on_publish(
            f"{IDENTITY}/{thing}/status/response",
            b'{"DeviceType": 1}',
            None,
            None,
            None,
        )
        assert "status" not in mqtt._mqtt_events.device_undecodable.get(thing, {})


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


class TestRefreshStatusPerDevice:
    def _mock_mqtt(self, api, execute_result):
        mock = MagicMock()
        mock.execute.return_value = execute_result
        mock.mqtt_events.mqtt_error_event.is_set.return_value = False
        mock.mqtt_events.device_status = {}
        mock.mqtt_events.device_support = {}
        mock.mqtt_events.device_shadow = {}
        mock.mqtt_events.device_undecodable = {}
        api._mqtt = mock
        return mock

    def test_one_undecodable_device_does_not_abort_the_other(self, api):
        a = api.things["Device A"].thing_name
        b = api.things["Device B"].thing_name
        mock = self._mock_mqtt(api, [[a, b], [a, b], [a, b], []])
        support = JciHitachiAWSStatusSupport(
            {"DeviceType": 1, "TemperatureSetting": 4128}
        )
        status = JciHitachiAWSStatus({"DeviceType": 1, "TemperatureSetting": 26})
        mock.mqtt_events.device_support = {b: support}
        mock.mqtt_events.device_shadow = {
            a: {"CleanNotification": True},
            b: {"CleanNotification": False},
        }
        mock.mqtt_events.device_status = {b: status}
        mock.mqtt_events.device_undecodable = {
            a: {
                "registration": (f"{IDENTITY}/{a}/registration/response", BINARY_FRAME),
                "status": (f"{IDENTITY}/{a}/status/response", BINARY_FRAME),
            }
        }

        api.refresh_status(refresh_support_code=True, refresh_shadow=True)  # no raise

        thing_a, thing_b = api.things["Device A"], api.things["Device B"]
        assert thing_a.available is False
        # unavailable because of the status channel, so the reason names that channel
        assert "not JSON (hex fcffff1f0101)" in thing_a.attention_reason
        assert "status/response" in thing_a.attention_reason
        assert thing_a.support_code is None and thing_a.status_code is None
        # the shadow channel did answer, so it is kept even though the device failed
        assert thing_a.shadow == {"CleanNotification": True}
        assert thing_b.available is True and thing_b.attention_reason is None
        assert thing_b.support_code is support and thing_b.status_code is status

        statuses = api.get_status()
        assert list(statuses) == ["Device B"], "never-refreshed devices are skipped"
        assert statuses["Device B"].max_temp == 32

    def test_status_without_support_code_keeps_devices_available(self, api, caplog):
        """2026-09-17 13:07: every unit answered registration with the frame, status with JSON."""
        a = api.things["Device A"].thing_name
        b = api.things["Device B"].thing_name
        mock = self._mock_mqtt(api, [[a, b], [], [a, b], []])
        status_a = JciHitachiAWSStatus({"DeviceType": 1, "CleanNotification": 0})
        status_b = JciHitachiAWSStatus({"DeviceType": 1, "CleanNotification": 0})
        mock.mqtt_events.device_status = {a: status_a, b: status_b}
        mock.mqtt_events.device_undecodable = {
            t: {"registration": (f"{IDENTITY}/{t}/registration/response", BINARY_FRAME)}
            for t in (a, b)
        }

        with caplog.at_level(logging.WARNING, logger="JciHitachi.api"):
            api.refresh_status(refresh_support_code=True)  # no raise

        for name, status in (("Device A", status_a), ("Device B", status_b)):
            thing = api.things[name]
            assert thing.available is True
            assert thing.status_code is status
            assert thing.support_code is None
            assert "registration/response" in thing.attention_reason
            assert "not JSON (hex fcffff1f0101)" in thing.attention_reason
        assert sorted(api.get_status()) == ["Device A", "Device B"]
        assert "Device A needs attention" in caplog.text
        assert "is unavailable" not in caplog.text

    def test_all_devices_failing_raises_device_error_listing_each(self, api):
        self._mock_mqtt(api, [[], [], [BaseException, BaseException], []])
        with pytest.raises(JciHitachiDeviceError) as exc:
            api.refresh_status()
        assert isinstance(exc.value, RuntimeError)
        assert "Device A" in str(exc.value) and "Device B" in str(exc.value)
        assert all(not t.available for t in api.things.values())

    def test_device_recovers_on_next_refresh(self, api):
        a = api.things["Device A"].thing_name
        api._things = {"Device A": api.things["Device A"]}
        mock = self._mock_mqtt(api, [[], [], [BaseException], []])
        with pytest.raises(JciHitachiDeviceError):
            api.refresh_status()
        assert api.things["Device A"].available is False

        mock.execute.return_value = [[], [], [a], []]
        mock.mqtt_events.device_status = {a: JciHitachiAWSStatus({"DeviceType": 1})}
        api.refresh_status()
        assert api.things["Device A"].available is True
        assert api.things["Device A"].attention_reason is None


class TestStructuredAttention:
    """`AWSThing.attention` mirrors `attention_reason`; the English strings stay unchanged."""

    def _api(self, api, execute_result):
        mock = TestRefreshStatusPerDevice._mock_mqtt(None, api, execute_result)
        api._things = {"Device A": api.things["Device A"]}
        return mock

    def test_undecodable_support_code(self, api):
        a = api.things["Device A"].thing_name
        mock = self._api(api, [[a], [], [a], []])
        mock.mqtt_events.device_status = {a: JciHitachiAWSStatus({"DeviceType": 1})}
        mock.mqtt_events.device_undecodable = {
            a: {"registration": (f"{IDENTITY}/{a}/registration/response", BINARY_FRAME)}
        }
        api.refresh_status(refresh_support_code=True)
        assert api.things["Device A"].attention == {
            "request": "support code",
            "topic": "registration/response",
            "cause": "undecodable",
            "payload_length": 6,
            "payload_hex": "fcffff1f0101",
        }

    def test_long_payload_hex_is_capped_at_64_bytes(self, api):
        a = api.things["Device A"].thing_name
        mock = self._api(api, [[a], [], [a], []])
        mock.mqtt_events.device_status = {a: JciHitachiAWSStatus({"DeviceType": 1})}
        long_payload = bytes(range(256)) * 3 + bytes(range(25))  # 793 bytes
        mock.mqtt_events.device_undecodable = {
            a: {"registration": (f"{IDENTITY}/{a}/registration/response", long_payload)}
        }
        api.refresh_status(refresh_support_code=True)
        attention = api.things["Device A"].attention
        assert attention["payload_length"] == 793
        assert attention["payload_hex"] == long_payload[:64].hex()

    def test_no_data_and_timeout(self, api):
        a = api.things["Device A"].thing_name
        mock = self._api(api, [[], [], [a], []])  # status "executed" but nothing stored
        with pytest.raises(JciHitachiDeviceError):
            api.refresh_status()
        thing = api.things["Device A"]
        assert thing.attention["cause"] == "no_data"
        assert thing.attention["topic"] == "status/response"
        assert thing.attention["payload_hex"] is None
        assert thing.attention_reason == (
            "An event occurred but wasn't accompanied with data when refreshing Device A status code."
        )

        mock.execute.return_value = [[], [], [BaseException], []]
        with pytest.raises(JciHitachiDeviceError):
            api.refresh_status()
        assert thing.attention["cause"] == "timeout"
        assert thing.attention_reason.startswith(
            "Timed out refreshing Device A status code."
        )

    def test_reason_names_the_status_failure_when_status_failed(self, api):
        """Code review finding: support undecodable + status timeout blamed the support code."""
        a = api.things["Device A"].thing_name
        mock = self._api(api, [[a], [], [BaseException], []])
        mock.mqtt_events.device_undecodable = {
            a: {"registration": (f"{IDENTITY}/{a}/registration/response", BINARY_FRAME)}
        }
        with pytest.raises(JciHitachiDeviceError):
            api.refresh_status(refresh_support_code=True)
        thing = api.things["Device A"]
        assert thing.available is False
        # every failed channel is named, the status one included; the structure points at status
        assert "registration/response" in thing.attention_reason
        assert "Timed out refreshing Device A status code." in thing.attention_reason
        assert thing.attention["cause"] == "timeout"
        assert thing.attention["topic"] == "status/response"

    def test_cleared_on_success(self, api):
        a = api.things["Device A"].thing_name
        mock = self._api(api, [[], [], [a], []])
        with pytest.raises(JciHitachiDeviceError):
            api.refresh_status()
        mock.mqtt_events.device_status = {a: JciHitachiAWSStatus({"DeviceType": 1})}
        api.refresh_status()
        assert api.things["Device A"].attention is None


class TestPublishForgetsPreviousUndecodable:
    """Code review finding: a previous non-JSON answer must not explain a later request."""

    def test_support_and_status_requests_clear_their_kind(self, mqtt):
        thing = f"{IDENTITY}_{GW_A}"
        mqtt._mqtt_events.device_undecodable[thing] = {
            "registration": (f"{IDENTITY}/{thing}/registration/response", BINARY_FRAME),
            "status": (f"{IDENTITY}/{thing}/status/response", BINARY_FRAME),
            "control": (f"{IDENTITY}/{thing}/control/response", BINARY_FRAME),
        }
        mqtt.publish(IDENTITY, thing, "support", 1)
        assert set(mqtt._mqtt_events.device_undecodable[thing]) == {"status", "control"}
        mqtt.publish(IDENTITY, thing, "status", 1)
        assert set(mqtt._mqtt_events.device_undecodable[thing]) == {"control"}
        # the queued publish coroutines are not run in this test
        for pool in (
            mqtt._execution_pools.support_execution_pool,
            mqtt._execution_pools.status_execution_pool,
        ):
            for coroutine in pool:
                coroutine.close()
            pool.clear()

    def test_next_poll_without_answer_is_no_data(self, api):
        a = api.things["Device A"].thing_name
        api._things = {"Device A": api.things["Device A"]}
        mock = TestRefreshStatusPerDevice._mock_mqtt(None, api, [[a], [], [a], []])
        mock.mqtt_events.device_status = {a: JciHitachiAWSStatus({"DeviceType": 1})}
        mock.mqtt_events.device_undecodable = {
            a: {"registration": (f"{IDENTITY}/{a}/registration/response", BINARY_FRAME)}
        }
        api.refresh_status(refresh_support_code=True)
        assert api.things["Device A"].attention["cause"] == "undecodable"

        # next poll: publish() forgot the frame, and no answer arrived at all
        mock.mqtt_events.device_undecodable = {a: {}}
        api.refresh_status(refresh_support_code=True)
        assert api.things["Device A"].attention["cause"] == "no_data"


class TestThingWithoutSupportCode:
    def test_properties_are_none_safe(self):
        thing = _thing("Device A", GW_A)
        assert thing.brand is None
        assert thing.model is None
        assert thing.firmware_version is None
        assert thing.firmware_code is None

    def test_corrupted_model_string_is_reported_as_unknown(self):
        # observed 2026-09-16 in a registration/response: "Model": "RAD-\xffR"
        thing = _thing("Device A", GW_A)
        thing.support_code = JciHitachiAWSStatusSupport(
            {"DeviceType": 1, "Model": "RAD-�\x06\x01R", "FirmwareVersion": "6.0.032"}
        )
        assert thing.model is None
        assert thing.firmware_version == "6.0.032"
        thing.support_code = JciHitachiAWSStatusSupport(
            {"DeviceType": 1, "Model": "RAD-90NF"}
        )
        assert thing.model == "RAD-90NF"


class TestNoStaleAnswers:
    def test_publish_forgets_the_previous_answer(self, mqtt):
        """A request must not be satisfied by the answer to the previous one (good-then-frame)."""
        thing = f"{IDENTITY}_{GW_A}"
        mqtt._mqtt_events.device_status[thing] = JciHitachiAWSStatus({"DeviceType": 1})
        mqtt._mqtt_events.device_support[thing] = JciHitachiAWSStatusSupport(
            {"DeviceType": 1}
        )
        mqtt._mqtt_events.device_control[thing] = {"Switch": 1}
        mqtt._mqtt_events.device_shadow[thing] = {"online": True}
        with patch.object(mqtt, "_mqttc"), patch.object(mqtt, "_shadow_mqttc"):
            mqtt.publish(IDENTITY, thing, "status")
            mqtt.publish(IDENTITY, thing, "support")
            mqtt.publish(IDENTITY, thing, "control", payload={})
            mqtt.publish_shadow(thing, "get", shadow_name="info")
        for pool in (
            mqtt._execution_pools.status_execution_pool,
            mqtt._execution_pools.support_execution_pool,
            mqtt._execution_pools.control_execution_pool,
            mqtt._execution_pools.shadow_execution_pool,
        ):
            for coro in pool:
                coro.close()
            pool.clear()
        assert thing not in mqtt._mqtt_events.device_status
        assert thing not in mqtt._mqtt_events.device_support
        assert thing not in mqtt._mqtt_events.device_control
        assert thing not in mqtt._mqtt_events.device_shadow

    def _control_mock(self, api, answered, on_execute):
        a = api.things["Device A"].thing_name
        api.things["Device A"].status_code = JciHitachiAWSStatus(
            {"DeviceType": 1, "Switch": 0}
        )
        mock = MagicMock()
        mock.mqtt_events.mqtt_error_event.is_set.return_value = False
        mock.mqtt_events.device_control = {}
        # a stale non-JSON control answer from an earlier request must not count
        mock.mqtt_events.device_undecodable = {
            a: {"control": (f"{IDENTITY}/{a}/control/response", b"stale")}
        }

        def execute(control=False):
            on_execute(mock.mqtt_events, a)  # the answer arrives while executing
            return [None, None, None, [a] if answered else []]

        mock.execute.side_effect = execute
        api._mqtt = mock
        return api.things["Device A"]

    def test_set_status_returns_false_on_undecodable_control_answer(self, api, caplog):
        def arrive(events, a):
            events.device_undecodable[a]["control"] = (
                f"{IDENTITY}/{a}/control/response",
                BINARY_FRAME,
            )

        thing = self._control_mock(api, True, arrive)
        with caplog.at_level(logging.WARNING):
            assert api.set_status("Switch", "Device A", status_str_value="on") is False
        assert "fcffff1f0101" in caplog.text
        assert thing.last_control_response == BINARY_FRAME
        assert thing.last_control_request["Switch"] == 1
        assert thing.last_control_at is not None

    def test_set_status_keeps_json_control_answer(self, api):
        def arrive(events, a):
            events.device_control[a] = {"Switch": 1, "TaskID": 1}

        thing = self._control_mock(api, True, arrive)
        assert api.set_status("Switch", "Device A", status_str_value="on") is True
        assert thing.last_control_response == {"Switch": 1, "TaskID": 1}
        assert thing.status_code.Switch == "on"

    def test_set_status_without_answer_forgets_stale_frame(self, api, caplog):
        thing = self._control_mock(api, False, lambda events, a: None)
        with caplog.at_level(logging.WARNING):
            assert api.set_status("Switch", "Device A", status_str_value="on") is False
        assert "did not answer the control request" in caplog.text
        assert thing.last_control_response is None


class TestCognitoErrorClassification:
    def test_only_credential_errors_are_auth_errors(self):
        from JciHitachi.aws_connection import cognito_error

        assert isinstance(
            cognito_error(
                "NotAuthorizedException Incorrect username or password.", "x"
            ),
            JciHitachiAuthError,
        )
        assert isinstance(
            cognito_error("UserNotFoundException User does not exist.", "x"),
            JciHitachiAuthError,
        )
        transient = cognito_error("TooManyRequestsException Rate exceeded", "x")
        assert isinstance(transient, RuntimeError)
        assert not isinstance(transient, JciHitachiAuthError)
        assert not isinstance(
            cognito_error("InternalErrorException", "x"), JciHitachiAuthError
        )


THINGS_JSON = {
    "results": {
        "Things": [
            {
                "DeviceType": "1",
                "ThingName": f"{IDENTITY}_{GW_A}",
                "CustomDeviceName": "Device A",
            }
        ]
    }
}


def _login_patches(refresh_side_effect):
    identity = MagicMock(identity_id=IDENTITY, host_identity_id=IDENTITY)
    return [
        patch("JciHitachi.aws_connection.GetUser.__init__", return_value=None),
        patch(
            "JciHitachi.aws_connection.GetUser.aws_tokens",
            new_callable=lambda: property(lambda self: MagicMock()),
        ),
        patch(
            "JciHitachi.aws_connection.GetUser.get_data", return_value=("OK", identity)
        ),
        patch(
            "JciHitachi.aws_connection.GetAllDevice.get_data",
            return_value=("OK", THINGS_JSON),
        ),
        patch("JciHitachi.aws_connection.JciHitachiAWSMqttConnection.configure"),
        patch(
            "JciHitachi.aws_connection.JciHitachiAWSMqttConnection.connect",
            return_value=True,
        ),
        patch(
            "JciHitachi.api.JciHitachiAWSAPI.refresh_status",
            side_effect=refresh_side_effect,
        ),
    ]


class TestLoginCleanup:
    def test_all_devices_failing_still_logs_in(self, api, caplog):
        patches = _login_patches(JciHitachiDeviceError("Device A timed out"))
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patch(
                "JciHitachi.aws_connection.JciHitachiAWSMqttConnection.disconnect"
            ) as disconnect,
            caplog.at_level(logging.WARNING),
        ):
            api.login()
        disconnect.assert_not_called()
        assert "no device is available yet" in caplog.text

    def test_unexpected_failure_disconnects_mqtt(self, api):
        patches = _login_patches(RuntimeError("boom"))
        with (
            patches[0],
            patches[1],
            patches[2],
            patches[3],
            patches[4],
            patches[5],
            patches[6],
            patch(
                "JciHitachi.aws_connection.JciHitachiAWSMqttConnection.disconnect"
            ) as disconnect,
        ):
            with pytest.raises(RuntimeError, match="boom"):
                api.login()
        disconnect.assert_called_once()

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
