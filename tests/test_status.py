import pytest

from JciHitachi.status import JciHitachiStatusInterpreter, JciHitachiCommandAC, JciHitachiCommandDH, JciHitachiAC, JciHitachiDH

from . import api, TEST_COMMAND_AC, TEST_DEVICE_AC, MOCK_CODE_AC, TEST_COMMAND_DH, TEST_DEVICE_DH, MOCK_CODE_DH


class TestACStatus:
    def test_supported_func(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_AC).decode_status()
        ac_status = JciHitachiAC(dev_status).status
        
        for each_stat in ac_status.values():
            assert each_stat != "unknown" and each_stat != None

    def test_unsupported_func(self):
        dev_status = {}
        ac_status = JciHitachiAC(dev_status).status
        for each_stat in ac_status.values():
            assert each_stat == "unsupported" or each_stat == -1
    
    def test_correctness(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_AC).decode_status()
        ac_status = JciHitachiAC(dev_status).status

        mock_status = {
            'power': 'off',
            'mode': 'cool',
            'air_speed': 'silent',
            'target_temp': 26,
            'indoor_temp': 26,
            'sleep_timer': 0,
            'vertical_wind_swingable': 'unsupported',
            'vertical_wind_direction': -1,
            'horizontal_wind_direction': 'unsupported',
            'mold_prev': 'disabled',
            'fast_op': 'disabled',
            'energy_save': 'disabled',
            'sound_prompt': 'enabled',
            'outdoor_temp': 24,
            'power_kwh': 0.0
        }

        for key, value in ac_status.items():
            assert key in mock_status
            assert mock_status[key] == value

    def test_command(self):
        commander = JciHitachiCommandAC('10416149025290813292')
        b64command = commander.get_command(TEST_COMMAND_AC, 0)
        
        mock_command = bytearray.fromhex(
                        "d0d100003c6a9dffff03e0d4ffffffff \
                        00000100000000000000002000010000 \
                        908D9859F3FD7f6c02000d278050f0d4 \
                        469dafd3605a6ebbdb130d278052f0d4 \
                        469dafd3605a6ebbdb13060006019E00 \
                        0099")
        assert b64command == mock_command

    @pytest.mark.slow("online test is a slow test.")
    def test_online(self, api):
        # Change sound prompt
        current_state = api.get_status()[TEST_DEVICE_AC]._status[JciHitachiAC.idx[TEST_COMMAND_AC]]
        if current_state != 1:
            changed_state = 1
        else:
            changed_state = 0
        assert api.set_status(TEST_COMMAND_AC, changed_state, TEST_DEVICE_AC)

        api.refresh_status() 
        assert api.get_status()[
            TEST_DEVICE_AC]._status[JciHitachiAC.idx[TEST_COMMAND_AC]] == changed_state
        
        # Change sound prompt back
        assert api.set_status(TEST_COMMAND_AC, current_state, TEST_DEVICE_AC)
        
        api.refresh_status()
        assert api.get_status()[
            TEST_DEVICE_AC]._status[JciHitachiAC.idx[TEST_COMMAND_AC]] == current_state


class TestDHStatus:
    def test_supported_func(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_DH).decode_status()
        dh_status = JciHitachiDH(dev_status).status

        for each_stat in dh_status.values():
            assert each_stat != "unknown" and each_stat != None

    def test_unsupported_func(self):
        dev_status = {}
        ac_status = JciHitachiDH(dev_status).status
        for each_stat in ac_status.values():
            assert each_stat == "unsupported" or each_stat == -1

    def test_correctness(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE_DH).decode_status()
        ac_status = JciHitachiDH(dev_status).status

        mock_status = {
            'power': 'on',
            'mode': 'custom',
            'target_humidity': 70,
            'indoor_humidity': 70,
            'wind_swingable': 'on',
            'water_full_warning': 'off',
            'clean_filter_notify': 'disabled',
            'air_purify_level': 'unsupported',  # not implemented
            'air_speed': 'silent',
            'side_vent': 'off',
            'sound_control': 'button+waterfull',
            'error_code': 0,
            'mold_prev': 'off',
            'power_kwh': 0.4,
            'air_quality_value': -1,  # not implemented
            'air_quality_level': 'unsupported',  # not implemented
            'pm25_value': 26,
            'display_brightness': 'bright',
            'odor_level': 'middle',
            'air_cleaning_filter': 'enabled'
        }

        for key, value in ac_status.items():
            assert key in mock_status
            assert mock_status[key] == value

    def test_command(self):
        commander = JciHitachiCommandDH('10416149025290813292')
        b64command = commander.get_command(TEST_COMMAND_DH, 0)

        mock_command = bytearray.fromhex(
            "d0d100003c6a9dffff03e0d4ffffffff \
                        00000100000000000000002000010000 \
                        908D9859F3FD7f6c02000d278050f0d4 \
                        469dafd3605a6ebbdb130d278052f0d4 \
                        469dafd3605a6ebbdb13060006049000 \
                        0092")
        assert b64command == mock_command

    @pytest.mark.skip("Skip online test as no usable account to test.")
    def test_online(self, api):
        # Change sound control
        current_state = api.get_status(
        )[TEST_DEVICE_DH]._status[JciHitachiDH.idx[TEST_COMMAND_DH]]
        if current_state != 1:
            changed_state = 1
        else:
            changed_state = 0
        assert api.set_status(TEST_COMMAND_DH, changed_state, TEST_DEVICE_DH)

        api.refresh_status()
        assert api.get_status()[
            TEST_DEVICE_DH]._status[JciHitachiDH.idx[TEST_COMMAND_DH]] == changed_state

        # Change Change sound control back
        assert api.set_status(TEST_COMMAND_DH, current_state, TEST_DEVICE_DH)

        api.refresh_status()
        assert api.get_status()[
            TEST_DEVICE_DH]._status[JciHitachiDH.idx[TEST_COMMAND_DH]] == current_state
