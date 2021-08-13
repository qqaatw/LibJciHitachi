import os

import pytest

from JciHitachi.api import JciHitachiAPI
from JciHitachi.status import JciHitachiStatusInterpreter, JciHitachiAC

TEST_EMAIL = os.environ['TEST_EMAIL']
TEST_PASSWORD = os.environ['TEST_PASSWORD']
TEST_DEVICE = os.environ['TEST_DEVICE']
MOCK_CODE = os.environ["MOCK_CODE"]

TEST_COMMAND = 'sound_prompt'

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
            'horizontal_wind_direction': -1,
            'mold_prev': 'disabled',
            'fast_op': 'disabled',
            'energy_save': 'disabled',
            'sound_prompt': 'enabled',
            'outdoor_temp': 24
        }

        for key, value in ac_status.items():
            assert key in mock_status
            assert mock_status[key] == value

    def test_ac_online(self):
        api = JciHitachiAPI(
            TEST_EMAIL,
            TEST_PASSWORD)
        api.login()
        
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