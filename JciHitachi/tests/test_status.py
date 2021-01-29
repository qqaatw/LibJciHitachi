import os

import pytest

from JciHitachi.status import JciHitachiStatusInterpreter, JciHitachiAC

MOCK_CODE = os.environ["MOCK_CODE"]


class TestACStatus:
    def test_normal(self):
        dev_status = JciHitachiStatusInterpreter(MOCK_CODE).decode_status()
        ac_status = JciHitachiAC(dev_status).status
        
        for each_stat in ac_status.values():
            assert each_stat != "unknown" and each_stat != None

    def test_code_length(self):
        with pytest.raises(AssertionError):
            dev_status = JciHitachiStatusInterpreter(
                MOCK_CODE[:-2])
