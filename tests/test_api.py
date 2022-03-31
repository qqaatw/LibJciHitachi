import time
from unittest.mock import MagicMock, patch

import pytest

from JciHitachi.api import AWSThing, JciHitachiAWSAPI
from JciHitachi.aws_connection import AWSTokens
from JciHitachi.model import (JciHitachiAWSStatus, JciHitachiAWSStatusSupport,
                              JciHitachiStatus)

from . import MOCK_GATEWAY_MAC, TEST_DEVICE_AC


@pytest.fixture()
def fixture_aws_mock_thing():
    thing = AWSThing(
        {
            "DeviceType": "1",
            "ThingName": f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}",
            "CustomDeviceName": TEST_DEVICE_AC
        }
    )
    thing.support_code = JciHitachiAWSStatusSupport({
        "Model": "RAD-90NF"
    })
    return thing

@pytest.fixture()
def fixture_aws_mock_api(fixture_aws_mock_thing):
    api = JciHitachiAWSAPI("", "")
    api._aws_tokens = AWSTokens("", "", "", time.time() + 3600)
    api._things = {TEST_DEVICE_AC: fixture_aws_mock_thing}
    api._things[TEST_DEVICE_AC].status_code = JciHitachiAWSStatus({
        "DeviceType": 1,
        "FanSpeed": 3,
    })
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
        statuses = api.get_status(TEST_DEVICE_AC)
        assert isinstance(statuses[TEST_DEVICE_AC], JciHitachiAWSStatus)
        assert statuses[TEST_DEVICE_AC].FanSpeed == "moderate"
        assert statuses[TEST_DEVICE_AC].status == {"DeviceType": "AC", "FanSpeed": "moderate"}

        # Test legacy status
        statuses = api.get_status(TEST_DEVICE_AC, legacy=True)
        assert isinstance(statuses[TEST_DEVICE_AC], JciHitachiAWSStatus)
        assert statuses[TEST_DEVICE_AC].air_speed == "moderate"
        assert statuses[TEST_DEVICE_AC].status == {"DeviceType": "AC", "air_speed": "moderate"}
        # Test not existing thing
        statuses = api.get_status("NON_EXISTING_NAME")
        assert statuses == {}
        # Test unknown device type
        with patch.object(api._things[TEST_DEVICE_AC], "_json") as mock_thing_json:
            mock_thing_json["DeviceType"] = "NON_EXISTING_TYPE"
            statuses = api.get_status(TEST_DEVICE_AC)
            assert statuses == {}

    def test_refresh_status(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_publish = MagicMock(return_value=None)
            mock_mqtt.publish = mock_publish
            mock_mqtt.mqtt_events.mqtt_error_event.is_set.return_value = False
            
            mock_mqtt.mqtt_events.device_status_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_support_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_shadow_event.wait.return_value = True
            api.refresh_status(TEST_DEVICE_AC, refresh_support_code=True, refresh_shadow=True)

            mock_mqtt.mqtt_events.device_status_event.wait.return_value = False
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {TEST_DEVICE_AC} status code."):
                api.refresh_status(TEST_DEVICE_AC)
            
            mock_mqtt.mqtt_events.device_support_event.wait.return_value = False
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {TEST_DEVICE_AC} support code."):
                api.refresh_status(TEST_DEVICE_AC, refresh_support_code=True)
            
            mock_mqtt.mqtt_events.device_shadow_event.wait.return_value = False
            with pytest.raises(RuntimeError, match=f"An error occurred when refreshing {TEST_DEVICE_AC} shadow."):
                api.refresh_status(TEST_DEVICE_AC, refresh_shadow=True)

    def test_set_status(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_publish = MagicMock(return_value = None)
            mock_mqtt.publish = mock_publish
            mock_mqtt.mqtt_events.mqtt_error_event.is_set.return_value = False

            mock_mqtt.mqtt_events.device_control_event.wait.return_value = True
            mock_mqtt.mqtt_events.device_control.get.return_value = {"FanSpeed": 3}
            # Test new name
            assert api.set_status("FanSpeed", device_name=TEST_DEVICE_AC, status_value=3)
            # Test legacy name
            assert api.set_status("air_speed", device_name=TEST_DEVICE_AC, status_value=3)
            # Test invalid status_name
            assert not api.set_status("invalid", device_name=TEST_DEVICE_AC, status_value=3)
            # Test invalid status_value
            assert not api.set_status("FanSpeed", device_name=TEST_DEVICE_AC, status_value=8)
            # Test status_str_value
            assert api.set_status("FanSpeed", device_name=TEST_DEVICE_AC, status_str_value="moderate")
            # Test invalid status_str_value
            assert not api.set_status("FanSpeed", device_name=TEST_DEVICE_AC, status_str_value="invalid")
            
            mock_mqtt.mqtt_events.device_control_event.wait.return_value = False
            assert not api.set_status("target_temp", device_name=TEST_DEVICE_AC, status_value=25)

    def test_get_monthly_data(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch("JciHitachi.aws_connection.GetAvailableAggregationMonthlyData.get_data") as mock_get_data:
            current_time = time.time()
            mock_get_data.return_value = ("OK", {"results": {"Data": [{"Timestamp": current_time + 300}, {"Timestamp": current_time}] }})

            assert api.get_monthly_data(2, TEST_DEVICE_AC) == [{"Timestamp": current_time}, {"Timestamp": current_time + 300}]

            mock_get_data.return_value = ("Not OK", {})

            with pytest.raises(RuntimeError, match=f"An error occurred when getting monthly data: Not OK"):
                api.get_monthly_data(2, TEST_DEVICE_AC)

class TestAWSThing:
    def test_repr(self, fixture_aws_mock_thing):
        thing = fixture_aws_mock_thing
        assert thing.__repr__() == f"""name: {TEST_DEVICE_AC}
brand: HITACHI
model: RAD-90NF
type: AC
available: True
status_code: None
support_code: {{'Model': 'RAD-90NF', 'Brand': 'HITACHI'}}
shadow: None
gateway_mac_address: {MOCK_GATEWAY_MAC}"""

    def test_from_device_names(self, fixture_aws_mock_thing):
        return