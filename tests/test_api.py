import time
from unittest.mock import MagicMock, patch

import pytest

from JciHitachi.api import AWSThing, JciHitachiAWSAPI
from JciHitachi.aws_connection import AWSTokens
from JciHitachi.model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

from . import MOCK_GATEWAY_MAC, MOCK_DEVICE_AC, MOCK_DEVICE_DH, MOCK_DEVICE_HE


@pytest.fixture()
def fixture_aws_mock_ac_thing():
    thing = AWSThing(
        {
            "DeviceType": "1",
            "ThingName": f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}",
            "CustomDeviceName": MOCK_DEVICE_AC,
        }
    )
    thing.status_code = JciHitachiAWSStatus({
        "DeviceType": 1,
        "FanSpeed": 4,  # high
        "TemperatureSetting": 26,
    })
    thing.support_code = JciHitachiAWSStatusSupport({
        "DeviceType": 1,
        "Model": "RAD-90NF",
        "FirmwareVersion": "6.0.035",
        "FanSpeed": 31,  # 0b11111
        "TemperatureSetting": 4128, # 32 16
    })
    return thing

@pytest.fixture()
def fixture_aws_mock_dh_thing():
    thing = AWSThing(
        {
            "DeviceType": "2",
            "ThingName": f"ap-northeast-1:9c8c1d20-b0d1-11ec-9f5a-644bf019ccc9_{MOCK_GATEWAY_MAC}",
            "CustomDeviceName": MOCK_DEVICE_DH,
        }
    )
    thing.status_code = JciHitachiAWSStatus({
        "DeviceType": 2,
        "Mode": 4,  # air_purify
    })
    thing.support_code = JciHitachiAWSStatusSupport({
        "DeviceType": 2,
        "Mode": 31,  # 0b11111
        "FirmwareVersion": "6.0.035",
        "Model": "RD-360HH",
    })
    return thing

@pytest.fixture()
def fixture_aws_mock_he_thing():
    thing = AWSThing(
        {
            "DeviceType": "3",
            "ThingName": f"ap-northeast-1:667bf9f1-9671-469b-adf3-935e4c982dc6_{MOCK_GATEWAY_MAC}",
            "CustomDeviceName": MOCK_DEVICE_HE,
        }
    )
    thing.status_code = JciHitachiAWSStatus({
        "DeviceType": 3,
        "BreathMode": 2,  # normal
    })
    thing.support_code = JciHitachiAWSStatusSupport({
        "DeviceType": 3,
        "BreathMode": 7,  # 0b111
        "FirmwareVersion": "6.0.036",
        "Model": "KPI-H",
    })
    return thing

@pytest.fixture()
def fixture_aws_mock_api(fixture_aws_mock_ac_thing, fixture_aws_mock_dh_thing, fixture_aws_mock_he_thing):
    api = JciHitachiAWSAPI("", "")
    api._aws_tokens = AWSTokens("", "", "", time.time() + 3600)
    api._things = {
        MOCK_DEVICE_AC: fixture_aws_mock_ac_thing,
        MOCK_DEVICE_DH: fixture_aws_mock_dh_thing,
        MOCK_DEVICE_HE: fixture_aws_mock_he_thing,
    }
    return api


class TestAWSAPI:
    def test_login(self, fixture_aws_mock_api):
        return

    def test_change_password(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch("JciHitachi.aws_connection.ChangePassword.get_data") as mock_get_data_1, \
            patch("JciHitachi.connection.UpdateUserCredential.get_data") as mock_get_data_2:
            mock_get_data_1.return_value = ("OK", "")
            mock_get_data_2.return_value = ("OK", "")
            api.change_password("new_password")

            mock_get_data_1.return_value = ("Not OK", "")
            with pytest.raises(RuntimeError, match=f"An error occurred when changing AWS Cognito password: Not OK"):
                api.change_password("new_password")
            
            mock_get_data_1.return_value = ("OK", "")
            mock_get_data_2.return_value = ("Not OK", "")
            with pytest.raises(RuntimeError, match=f"An error occurred when changing Hitachi password: Not OK"):
                api.change_password("new_password")

    def test_get_status(self, fixture_aws_mock_api):
        # Test status
        api = fixture_aws_mock_api
        statuses = api.get_status()
        assert isinstance(statuses[MOCK_DEVICE_AC], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_AC].FanSpeed == "high"
        assert statuses[MOCK_DEVICE_AC].status == {"DeviceType": "AC", "FanSpeed": "high", "TemperatureSetting": 26, "max_temp": 32, "min_temp": 16}
        assert isinstance(statuses[MOCK_DEVICE_DH], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_DH].Mode == "air_purify"
        assert statuses[MOCK_DEVICE_DH].status == {"DeviceType": "DH", "Mode": "air_purify", 'max_humidity': 70, 'min_humidity': 40}
        assert isinstance(statuses[MOCK_DEVICE_HE], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_HE].BreathMode == "normal"
        assert statuses[MOCK_DEVICE_HE].status == {"DeviceType": "HE", "BreathMode": "normal"}

        # Test legacy status
        statuses = api.get_status(legacy=True)
        assert isinstance(statuses[MOCK_DEVICE_AC], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_AC].air_speed == "high"
        assert statuses[MOCK_DEVICE_AC].status == {"DeviceType": "AC", "air_speed": "high", "target_temp": 26, 'max_temp': 32, 'min_temp': 16}
        assert isinstance(statuses[MOCK_DEVICE_DH], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_DH].mode == "air_purify"
        assert statuses[MOCK_DEVICE_DH].status == {"DeviceType": "DH", "mode": "air_purify", 'max_humidity': 70, 'min_humidity': 40}
        assert isinstance(statuses[MOCK_DEVICE_HE], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_HE].BreathMode == "normal"
        assert statuses[MOCK_DEVICE_HE].status == {"DeviceType": "HE", "BreathMode": "normal"}

        # Test not existing thing
        statuses = api.get_status("NON_EXISTING_NAME")
        assert statuses == {}

        # Test unknown device type
        with patch.object(api._things[MOCK_DEVICE_AC], "_json") as mock_thing_json:
            mock_thing_json["DeviceType"] = "NON_EXISTING_TYPE"
            statuses = api.get_status(MOCK_DEVICE_AC)
            assert statuses == {}

    def test_refresh_status(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_publish = MagicMock(return_value=None)
            mock_mqtt.publish = mock_publish
            mock_mqtt.mqtt_events.mqtt_error_event.is_set.return_value = False
            
            mock_mqtt.mqtt_events.device_status = {api.things[MOCK_DEVICE_AC].thing_name : ""}
            mock_mqtt.mqtt_events.device_support = {api.things[MOCK_DEVICE_AC].thing_name : ""}
            mock_mqtt.mqtt_events.device_shadow = {api.things[MOCK_DEVICE_AC].thing_name : ""}
            mock_mqtt.mqtt_events.device_status_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_support_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_shadow_event.wait.return_value = True
            api.refresh_status(MOCK_DEVICE_AC, refresh_support_code=True, refresh_shadow=True)

            # status event timeout
            mock_mqtt.mqtt_events.device_status_event.wait.return_value = False
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {MOCK_DEVICE_AC} status code."):
                api.refresh_status(MOCK_DEVICE_AC)
            
            # status not stored in dict
            mock_mqtt.mqtt_events.device_status_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_status = {}
            with pytest.raises(RuntimeError, match=f"An event occurred but wasn't accompanied with data when refreshing {MOCK_DEVICE_AC} status code."):
                api.refresh_status(MOCK_DEVICE_AC)

            # support event timeout
            mock_mqtt.mqtt_events.device_support_event.wait.return_value = False
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {MOCK_DEVICE_AC} support code."):
                api.refresh_status(MOCK_DEVICE_AC, refresh_support_code=True)
            
            # support not stored in dict
            mock_mqtt.mqtt_events.device_support_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_support = {}
            with pytest.raises(RuntimeError, match=f"An event occurred but wasn't accompanied with data when refreshing {MOCK_DEVICE_AC} support code."):
                api.refresh_status(MOCK_DEVICE_AC, refresh_support_code=True)
            
            # shadow event timeout
            mock_mqtt.mqtt_events.device_shadow_event.wait.return_value = False
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {MOCK_DEVICE_AC} shadow."):
                api.refresh_status(MOCK_DEVICE_AC, refresh_shadow=True)

            # shadow not stored in dict
            mock_mqtt.mqtt_events.device_shadow_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_shadow = {}
            with pytest.raises(RuntimeError, match=f"An event occurred but wasn't accompanied with data when refreshing {MOCK_DEVICE_AC} shadow."):
                api.refresh_status(MOCK_DEVICE_AC, refresh_shadow=True)

    def test_set_status(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_publish = MagicMock(return_value = None)
            mock_mqtt.publish = mock_publish
            mock_mqtt.mqtt_events.mqtt_error_event.is_set.return_value = False

            mock_mqtt.mqtt_events.device_control_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_control.get.return_value = {"FanSpeed": 3}

            assert api.set_status("FanSpeed", device_name=MOCK_DEVICE_AC, status_value=3)
            assert api.things[MOCK_DEVICE_AC].status_code.FanSpeed == "moderate"

            # Test legacy name
            assert api.set_status("air_speed", device_name=MOCK_DEVICE_AC, status_value=3)
            # Test invalid status_name
            assert not api.set_status("invalid", device_name=MOCK_DEVICE_AC, status_value=3)
            # Test invalid status_value
            assert not api.set_status("FanSpeed", device_name=MOCK_DEVICE_AC, status_value=8)
            # Test status_str_value
            assert api.set_status("FanSpeed", device_name=MOCK_DEVICE_AC, status_str_value="moderate")
            # Test invalid status_str_value
            assert not api.set_status("FanSpeed", device_name=MOCK_DEVICE_AC, status_str_value="invalid")
            
            mock_mqtt.mqtt_events.device_control_event.wait.return_value = False
            assert not api.set_status("target_temp", device_name=MOCK_DEVICE_AC, status_value=25)

    def test_refresh_monthly_data(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch("JciHitachi.aws_connection.GetAvailableAggregationMonthlyData.get_data") as mock_get_data:
            current_time = time.time()
            mock_get_data.return_value = ("OK", {"results": {"Data": [{"Timestamp": current_time + 300}, {"Timestamp": current_time}] }})

            assert api.things[MOCK_DEVICE_AC].monthly_data == None
            api.refresh_monthly_data(2, MOCK_DEVICE_AC)
            assert api.things[MOCK_DEVICE_AC].monthly_data == [{"Timestamp": current_time}, {"Timestamp": current_time + 300}]

            mock_get_data.return_value = ("Not OK", {})

            with pytest.raises(RuntimeError, match=f"An error occurred when getting monthly data: Not OK"):
                api.refresh_monthly_data(2, MOCK_DEVICE_AC)

class TestAWSThing:
    def test_repr(self, fixture_aws_mock_ac_thing, fixture_aws_mock_dh_thing, fixture_aws_mock_he_thing):
        ac_thing = fixture_aws_mock_ac_thing
        assert ac_thing.__repr__() == f"""name: {MOCK_DEVICE_AC}
brand: HITACHI
model: RAD-90NF
type: AC
firmware_code: unsupported
firmawre_version: 6.0.035
available: True
status_code: {{'DeviceType': 'AC', 'FanSpeed': 'high', 'TemperatureSetting': 26}}
support_code: {{'DeviceType': 'AC', 'Model': 'RAD-90NF', 'FirmwareVersion': '6.0.035', 'FanSpeed': 31, 'TemperatureSetting': 4128, 'Brand': 'HITACHI', 'max_temp': 32, 'min_temp': 16}}
shadow: None
gateway_mac_address: {MOCK_GATEWAY_MAC}"""

        dh_thing = fixture_aws_mock_dh_thing
        assert dh_thing.__repr__() == f"""name: {MOCK_DEVICE_DH}
brand: HITACHI
model: RD-360HH
type: DH
firmware_code: unsupported
firmawre_version: 6.0.035
available: True
status_code: {{'DeviceType': 'DH', 'Mode': 'air_purify'}}
support_code: {{'DeviceType': 'DH', 'Mode': 31, 'FirmwareVersion': '6.0.035', 'Model': 'RD-360HH', 'Brand': 'HITACHI', 'max_humidity': 70, 'min_humidity': 40}}
shadow: None
gateway_mac_address: {MOCK_GATEWAY_MAC}"""

        he_thing = fixture_aws_mock_he_thing
        assert he_thing.__repr__() == f"""name: {MOCK_DEVICE_HE}
brand: HITACHI
model: KPI-H
type: HE
firmware_code: unsupported
firmawre_version: 6.0.036
available: True
status_code: {{'DeviceType': 'HE', 'BreathMode': 'normal'}}
support_code: {{'DeviceType': 'HE', 'BreathMode': 7, 'FirmwareVersion': '6.0.036', 'Model': 'KPI-H', 'Brand': 'HITACHI'}}
shadow: None
gateway_mac_address: {MOCK_GATEWAY_MAC}"""

    def test_from_device_names(self, fixture_aws_mock_ac_thing):
        return