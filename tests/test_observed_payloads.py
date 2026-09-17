"""Run the library against payloads captured from the real cloud (see fixtures/observed_2026_09_16/README.md)."""

import json
import threading
from pathlib import Path

import pytest

from JciHitachi.api import AWSThing
from JciHitachi.aws_connection import JciHitachiAWSMqttConnection
from JciHitachi.model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

FIXTURES = Path(__file__).parent / "fixtures" / "observed_2026_09_16"
IDENTITY = "<identity>"


def _bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _topic(gw: str, kind: str) -> str:
    return f"{IDENTITY}/{IDENTITY}_{gw}/{kind}/response"


@pytest.fixture()
def mqtt():
    return JciHitachiAWSMqttConnection(lambda: None)


class TestGetAllDevice:
    def test_three_things_without_model(self):
        things = AWSThing.from_device_names(
            json.loads(_bytes("get_all_device.json")), None
        )
        assert sorted(things) == ["Device A", "Device B", "Device C"]
        for thing in things.values():
            assert thing.type == "AC"
            assert thing.model is None  # no support code yet
            assert thing.available is True and thing.attention_reason is None


class TestIdleUnitRegistrationResponse:
    """The normal support-code answer carries a raw 0xFF byte inside "Model"."""

    @pytest.mark.parametrize("gw", ["gw-A", "gw-B"])
    def test_is_not_valid_utf8_but_decodes_with_replace(self, mqtt, gw):
        payload = _bytes(f"registration_response_{gw}.json")
        assert b"\xff" in payload
        with pytest.raises(UnicodeDecodeError):
            payload.decode("utf-8")

        thing_name = f"{IDENTITY}_{gw}"
        mqtt._mqtt_events.device_support_event[thing_name] = threading.Event()
        mqtt._on_publish(_topic(gw, "registration"), payload, None, None, None)

        support = mqtt._mqtt_events.device_support[thing_name]
        assert isinstance(support, JciHitachiAWSStatusSupport)
        assert support.FirmwareVersion == "6.0.032"
        assert (
            support.max_temp == 32 and support.min_temp == 16
        )  # TemperatureSetting 4128
        assert thing_name not in mqtt._mqtt_events.device_undecodable

    def test_model_is_reported_unknown_not_garbage(self):
        thing = AWSThing(
            {
                "DeviceType": "1",
                "ThingName": f"{IDENTITY}_gw-B",
                "CustomDeviceName": "Device B",
            }
        )
        thing.support_code = JciHitachiAWSStatusSupport(
            json.loads(
                _bytes("registration_response_gw-B.json").decode(errors="replace")
            )
        )
        assert thing.model is None
        assert thing.brand == "HITACHI"
        assert thing.firmware_version == "6.0.032"
        assert thing.firmware_code == 53


class TestRunningUnitRegistrationResponse:
    def test_six_byte_frame_is_recorded_per_kind(self, mqtt):
        frame = _bytes("registration_response_gw-C_running.bin")
        assert frame == b"\xfc\xff\xff\x1f\x01\x01"
        thing_name = f"{IDENTITY}_gw-C"
        mqtt._mqtt_events.device_support_event[thing_name] = threading.Event()
        mqtt._mqtt_events.mqtt_error_event.clear()

        mqtt._on_publish(_topic("gw-C", "registration"), frame, None, None, None)
        mqtt._on_publish(
            _topic("gw-C", "status-secondary"),
            _bytes("status-secondary_response_gw-C_running.bin"),
            None,
            None,
            None,
        )

        recorded = mqtt._mqtt_events.device_undecodable[thing_name]
        assert set(recorded) == {"registration", "status-secondary"}
        assert recorded["registration"] == (_topic("gw-C", "registration"), frame)
        assert mqtt._mqtt_events.device_support_event[thing_name].is_set()
        assert thing_name not in mqtt._mqtt_events.device_support
        assert not mqtt._mqtt_events.mqtt_error_event.is_set()


class TestStatusResponses:
    @pytest.mark.parametrize(
        "gw, switch, clean_notification",
        [("gw-A", 0, 1), ("gw-B", 0, 1), ("gw-C", 1, 0)],
    )
    def test_status_fields(self, mqtt, gw, switch, clean_notification):
        thing_name = f"{IDENTITY}_{gw}"
        mqtt._on_publish(
            _topic(gw, "status"), _bytes(f"status_response_{gw}.json"), None, None, None
        )
        status = mqtt._mqtt_events.device_status[thing_name]
        assert isinstance(status, JciHitachiAWSStatus)
        assert status.Switch == ("on" if switch else "off")
        # numeric status field; at capture time the official app showed the freeze-clean
        # prompt for exactly the units reporting 1 (A, B) and not for C
        assert status.CleanNotification == clean_notification
        assert status.legacy_status.CleanNotification == clean_notification

    def test_running_unit_status_is_json_even_when_registration_is_not(self, mqtt):
        # same capture: gw-C answered registration with the 6-byte frame (above) but status with JSON
        thing_name = f"{IDENTITY}_gw-C"
        mqtt._on_publish(
            _topic("gw-C", "status"),
            _bytes("status_response_gw-C.json"),
            None,
            None,
            None,
        )
        assert mqtt._mqtt_events.device_status[thing_name].Switch == "on"


class TestShadowInfo:
    def test_flags_are_true_for_every_unit_regardless_of_status(self):
        shadows = json.loads(_bytes("shadow_info_get_accepted.json"))
        assert len(shadows) == 3
        for s in shadows:
            assert s["reported"]["online"] is True
            assert s["reported"]["CleanNotification"] is True
            assert s["reported"]["CleanFilterNotification"] is True
        # so the shadow flag cannot be used as "notification pending" (cf. status above)
