import pytest

from JciHitachi.status import JciHitachiStatusInterpreter, JciHitachiCommandAC, JciHitachiAC

from . import api, TEST_DEVICE, MOCK_CODE, TEST_COMMAND


class TestACStatus:
    def test_supported_func(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE).decode_status()
        ac_status = JciHitachiAC(dev_status).status
        
        for each_stat in ac_status.values():
            assert each_stat != "unknown" and each_stat != None

    def test_unsupported_func(self):
        dev_status = {}
        ac_status = JciHitachiAC(dev_status).status
        for each_stat in ac_status.values():
            assert each_stat == "unsupported" or each_stat == -1
    
    def test_correctness(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE).decode_status()
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
            'outdoor_temp': 24
        }

        for key, value in ac_status.items():
            assert key in mock_status
            assert mock_status[key] == value

    def test_command(self):
        commander = JciHitachiCommandAC('10416149025290813292')
        b64command = commander.get_command(TEST_COMMAND, 0)
        
        mock_command = bytearray.fromhex(
                        "d0d100003c6a9dffff03e0d4ffffffff \
                        00000100000000000000002000010000 \
                        908D9859F3FD7f6c02000d278050f0d4 \
                        469dafd3605a6ebbdb130d278052f0d4 \
                        469dafd3605a6ebbdb13060006019E00 \
                        0099")
        assert b64command == mock_command

    pytest.mark.skip("Skip online test.")
    def test_ac_online(self, api):
        # Change sound prompt
        current_state = api.get_status()[TEST_DEVICE]._status[JciHitachiAC.idx[TEST_COMMAND]]
        if current_state != 1:
            changed_state = 1
        else:
            changed_state = 0
        assert api.set_status(TEST_COMMAND, changed_state, TEST_DEVICE)

        api.refresh_status() 
        assert api.get_status()[
            TEST_DEVICE]._status[JciHitachiAC.idx[TEST_COMMAND]] == changed_state
        
        # Change sound prompt back
        assert api.set_status(TEST_COMMAND, current_state, TEST_DEVICE)
        
        api.refresh_status()
        assert api.get_status()[
            TEST_DEVICE]._status[JciHitachiAC.idx[TEST_COMMAND]] == current_state
