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
            TEST_PASSWORD,
            TEST_DEVICE,
            device_type="AC")
        api.login()
        
        # Change air speed
        current_air_speed = api.get_status()._status[JciHitachiAC.idx['air_speed']]
        if current_air_speed != 4:
            next_air_speed = 4
        else:
            next_air_speed = 3
        assert api.set_status('air_speed', next_air_speed)
        # The API seems to be delayed to update status, so wait for 1.5 sec.
        time.sleep(1.5)
        api.refresh_status() 
        assert api.get_status()._status[JciHitachiAC.idx['air_speed']] == next_air_speed
        
        # Change air speed back
        assert api.set_status('air_speed', current_air_speed)
        # The API seems to be delayed to update status, so wait for 1.5 sec.
        time.sleep(1.5)
        api.refresh_status()
        assert api.get_status()._status[JciHitachiAC.idx['air_speed']] == current_air_speed

    def test_code_length(self):
        with pytest.raises(AssertionError):
            dev_status = JciHitachiStatusInterpreter(MOCK_CODE[:-2])
