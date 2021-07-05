import os
import time

import pytest

from JciHitachi.api import JciHitachiAPI
from JciHitachi.status import JciHitachiStatusInterpreter, JciHitachiAC

TEST_EMAIL = os.environ['TEST_EMAIL']
TEST_PASSWORD = os.environ['TEST_PASSWORD']
TEST_DEVICE = os.environ['TEST_DEVICE']
MOCK_CODE = os.environ["MOCK_CODE"]


class TestACStatus:
    def test_offline(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE).decode_status()
        ac_status = JciHitachiAC(dev_status).status
        
        for each_stat in ac_status.values():
            assert each_stat != "unknown" and each_stat != None

    def test_online(self):
        api = JciHitachiAPI(
            TEST_EMAIL,
            TEST_PASSWORD)
        api.login()
        
        # Change air speed
        current_air_speed = api.get_status()[TEST_DEVICE]._status[JciHitachiAC.idx['air_speed']]
        if current_air_speed != 2:
            next_air_speed = 2
        else:
            next_air_speed = 1
        assert api.set_status('air_speed', next_air_speed, TEST_DEVICE)

        api.refresh_status() 
        assert api.get_status()[TEST_DEVICE]._status[JciHitachiAC.idx['air_speed']] == next_air_speed
        
        # Change air speed back
        assert api.set_status('air_speed', current_air_speed, TEST_DEVICE)
        
        api.refresh_status()
        assert api.get_status()[TEST_DEVICE]._status[JciHitachiAC.idx['air_speed']] == current_air_speed

    def test_code_length(self):
        with pytest.raises(AssertionError):
            dev_status = JciHitachiStatusInterpreter(MOCK_CODE[:-2])
