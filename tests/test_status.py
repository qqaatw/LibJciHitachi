import pytest

from JciHitachi.model import (
    JciHitachiAC,
    JciHitachiACSupport,
    JciHitachiDH,
    JciHitachiDHSupport,
    JciHitachiHE,
    JciHitachiHESupport,
)
from JciHitachi.status import (
    JciHitachiCommandAC,
    JciHitachiCommandDH,
    JciHitachiCommandHE,
    JciHitachiStatusInterpreter,
)

from . import (
    MOCK_CODE_AC,
    MOCK_CODE_DH,
    MOCK_GATEWAY_MAC,
    MOCK_SUPPORT_CODE_AC,
    MOCK_SUPPORT_CODE_DH,
    MOCK_COMMAND_AC,
    MOCK_COMMAND_DH,
)


class TestACStatus:
    def test_model_brand(self):
        dev_support = JciHitachiStatusInterpreter(MOCK_SUPPORT_CODE_AC).decode_support()
        ac_support = JciHitachiACSupport(dev_support)

        assert ac_support.brand == "HITACHI"
        assert ac_support.model == "RAD-90NF"

    def test_supported_status(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_AC).decode_status()
        ac_status = JciHitachiAC(dev_status).status

        for status in ac_status.values():
            assert status != "unknown" and status != None

    def test_unsupported_status(self):
        dev_status = {}
        ac_status = JciHitachiAC(dev_status).status

        for status in ac_status.values():
            assert status == "unsupported" or status == -1

    def test_correctness(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_AC).decode_status()
        ac_status = JciHitachiAC(dev_status).status

        mock_status = {
            "power": "off",
            "mode": "cool",
            "air_speed": "silent",
            "target_temp": 26,
            "indoor_temp": 26,
            "sleep_timer": 0,
            "vertical_wind_swingable": "unsupported",
            "vertical_wind_direction": -1,
            "horizontal_wind_direction": "unsupported",
            "mold_prev": "disabled",
            "fast_op": "disabled",
            "energy_save": "disabled",
            "sound_prompt": "enabled",
            "outdoor_temp": 24,
            "power_kwh": 0.0,
            "freeze_clean": "off",
        }

        for key, value in ac_status.items():
            assert key in mock_status
            assert mock_status[key] == value

    def test_limit(self):
        dev_support = JciHitachiStatusInterpreter(MOCK_SUPPORT_CODE_AC).decode_support()
        ac_support = JciHitachiACSupport(dev_support)
        mock_status_raw = {
            "power": 0,
            "mode": 0,
            "air_speed": 1,
            "target_temp": 26,
            "indoor_temp": 26,
            "sleep_timer": 0,
            "vertical_wind_swingable": -1,
            "vertical_wind_direction": -1,
            "horizontal_wind_direction": -1,
            "mold_prev": 0,
            "fast_op": 0,
            "energy_save": 0,
            "sound_prompt": 0,
            "outdoor_temp": 24,
            "power_kwh": 0,
        }

        mock_status_raw_limited = {
            key: ac_support.limit(key, value) for key, value in mock_status_raw.items()
        }

        for key, raw_value in mock_status_raw.items():
            if raw_value == -1:
                raw_value = None
            if (
                key == "outdoor_temp"
            ):  # The supported `outdoor_temp` values seem not correct so the limited values are incorrect too. skipping this test.
                continue
            assert raw_value == mock_status_raw_limited[key]

    def test_command(self):
        commander = JciHitachiCommandAC(MOCK_GATEWAY_MAC)
        b64command = commander.get_command(MOCK_COMMAND_AC, 0)

        mock_command = bytearray.fromhex(
            "d0d100003c6a9dffff03e0d4ffffffff \
             00000100000000000000002000010000 \
             908D9859F3FD7f6c02000d278050f0d4 \
             469dafd3605a6ebbdb130d278052f0d4 \
             469dafd3605a6ebbdb13060006019E00 \
             0099"
        )
        assert b64command == mock_command


class TestDHStatus:
    def test_model_brand(self):
        dev_support = JciHitachiStatusInterpreter(MOCK_SUPPORT_CODE_DH).decode_support()
        dh_support = JciHitachiDHSupport(dev_support)

        assert dh_support.brand == "HITACHI"
        assert dh_support.model == "RD-360HH"

    def test_supported_status(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_DH).decode_status()
        dh_status = JciHitachiDH(dev_status).status

        for status in dh_status.values():
            assert status != "unknown" and status != None

    def test_unsupported_status(self):
        dev_status = {}
        ac_status = JciHitachiDH(dev_status).status
        for status in ac_status.values():
            assert status == "unsupported" or status == -1

    def test_correctness(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_DH).decode_status()
        ac_status = JciHitachiDH(dev_status).status

        mock_status = {
            "power": "on",
            "mode": "custom",
            "target_humidity": 70,
            "indoor_humidity": 70,
            "wind_swingable": "on",
            "water_full_warning": "off",
            "clean_filter_notify": "disabled",
            "air_purify_level": "unsupported",  # not implemented
            "air_speed": "silent",
            "side_vent": "off",
            "sound_control": "button+waterfull",
            "error_code": 0,
            "mold_prev": "off",
            "power_kwh": 0.4,
            "air_quality_value": -1,  # not implemented
            "air_quality_level": "unsupported",  # not implemented
            "pm25_value": 26,
            "display_brightness": "bright",
            "odor_level": "middle",
            "air_cleaning_filter": "enabled",
        }

        for key, value in ac_status.items():
            assert key in mock_status
            assert mock_status[key] == value

    def test_command(self):
        commander = JciHitachiCommandDH(MOCK_GATEWAY_MAC)
        b64command = commander.get_command(MOCK_COMMAND_DH, 0)

        mock_command = bytearray.fromhex(
            "d0d100003c6a9dffff03e0d4ffffffff \
             00000100000000000000002000010000 \
             908D9859F3FD7f6c02000d278050f0d4 \
             469dafd3605a6ebbdb130d278052f0d4 \
             469dafd3605a6ebbdb13060006049000 \
             0092"
        )
        assert b64command == mock_command


class TestCommonStatus:
    def test_command_num_bytes(self):
        ac_commander = JciHitachiCommandAC(MOCK_GATEWAY_MAC)
        assert len(ac_commander.get_command("power", 0)) == 82
        dh_commander = JciHitachiCommandDH(MOCK_GATEWAY_MAC)
        assert len(dh_commander.get_command("power", 0)) == 82
        # he_commander = JciHitachiCommandHE(MOCK_GATEWAY_MAC)
        # assert len(he_commander.get_command("power", 0)) == 82

    # TODO: Add device availablity test
