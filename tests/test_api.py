import time
from unittest.mock import MagicMock, patch

import pytest

from JciHitachi.api import AWSThing, JciHitachiAWSAPI
from JciHitachi.aws_connection import AWSTokens, AWSIdentity
from JciHitachi.model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

from . import MOCK_GATEWAY_MAC, MOCK_DEVICE_AC, MOCK_DEVICE_DH, MOCK_DEVICE_HE


MOCK_THINGS_JSON = {
    "results": {
        "Things": [
            {
                "DeviceType": "1",
                "ThingName": f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}",
                "CustomDeviceName": MOCK_DEVICE_AC,
            },
            {
                "DeviceType": "2",
                "ThingName": f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}",
                "CustomDeviceName": MOCK_DEVICE_DH,
            },
        ]
    }
}


@pytest.fixture()
def fixture_aws_mock_ac_thing():
    thing = AWSThing(
        {
            "DeviceType": "1",
            "ThingName": f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}",
            "CustomDeviceName": MOCK_DEVICE_AC,
        }
    )
    thing.status_code = JciHitachiAWSStatus(
        {
            "DeviceType": 1,
            "FanSpeed": 4,  # high
            "TemperatureSetting": 26,
        }
    )
    thing.support_code = JciHitachiAWSStatusSupport(
        {
            "DeviceType": 1,
            "Model": "RAD-90NF",
            "FirmwareVersion": "6.0.035",
            "FanSpeed": 31,  # 0b11111
            "TemperatureSetting": 4128,  # 32 16
        }
    )
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
    thing.status_code = JciHitachiAWSStatus(
        {
            "DeviceType": 2,
            "Mode": 4,  # air_purify
        }
    )
    thing.support_code = JciHitachiAWSStatusSupport(
        {
            "DeviceType": 2,
            "Mode": 31,  # 0b11111
            "FirmwareVersion": "6.0.035",
            "Model": "RD-360HH",
        }
    )
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
    thing.status_code = JciHitachiAWSStatus(
        {
            "DeviceType": 3,
            "BreathMode": 2,  # normal
        }
    )
    thing.support_code = JciHitachiAWSStatusSupport(
        {
            "DeviceType": 3,
            "BreathMode": 7,  # 0b111
            "FirmwareVersion": "6.0.036",
            "Model": "KPI-H",
        }
    )
    return thing


@pytest.fixture()
def fixture_aws_mock_api(
    fixture_aws_mock_ac_thing, fixture_aws_mock_dh_thing, fixture_aws_mock_he_thing
):
    api = JciHitachiAWSAPI("", "")
    api._aws_tokens = AWSTokens("", "", "", time.time() + 3600)
    api._things = {
        MOCK_DEVICE_AC: fixture_aws_mock_ac_thing,
        MOCK_DEVICE_DH: fixture_aws_mock_dh_thing,
        MOCK_DEVICE_HE: fixture_aws_mock_he_thing,
    }
    return api


@pytest.fixture()
def fixture_aws_identity():
    # dummy identity
    return AWSIdentity("id", "host_id", "username", {"attr", "attr"})


class TestAWSAPI:
    def test_login(self, fixture_aws_mock_api, fixture_aws_identity):
        api = fixture_aws_mock_api
        with patch(
            "JciHitachi.aws_connection.GetUser.get_data"
        ) as mock_get_data_get_user, patch(
            "JciHitachi.aws_connection.GetUser.login"
        ) as mock_login_get_user, patch(
            "JciHitachi.aws_connection.ListSubUser.get_data"
        ) as mock_get_data_list_subuser, patch(
            "JciHitachi.aws_connection.GetAllDevice.get_data"
        ) as mock_get_data_get_all_device, patch(
            "JciHitachi.aws_connection.JciHitachiAWSMqttConnection.connect"
        ) as mock_connect_mqtt:
            # initialization
            aws_tokens = api._aws_tokens
            api._aws_tokens = None
            mock_get_data_get_user.return_value = (
                "OK",
                fixture_aws_identity,
            )
            mock_login_get_user.return_value = ("OK", aws_tokens)

            # mock_get_data_list_subuser currently unused.
            mock_get_data_list_subuser.return_value = (
                "OK",
                {
                    "results": {
                        "FamilyMemberList": [
                            {"userId": "uid1", "isHost": False},
                            {"userId": "uid2", "isHost": True},
                        ]
                    }
                },
            )
            mock_get_data_get_all_device.return_value = ("OK", MOCK_THINGS_JSON)
            mock_connect_mqtt.return_value = True
            api.refresh_status = MagicMock()
            assert api._aws_tokens is None
            assert api._aws_identity is None
            assert len(api._things) == 3
            assert api.device_names is None

            # normal case
            api.login()
            assert api._aws_tokens == aws_tokens
            assert api._aws_identity is not None
            assert api._aws_identity.identity_id == "id"
            assert api._aws_identity.host_identity_id == "host_id"
            assert len(api._things) == 2
            assert len(api.device_names) == 2

    def test_change_password(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch(
            "JciHitachi.aws_connection.ChangePassword.get_data"
        ) as mock_get_data_1, patch(
            "JciHitachi.connection.UpdateUserCredential.get_data"
        ) as mock_get_data_2:
            mock_get_data_1.return_value = ("OK", "")
            mock_get_data_2.return_value = ("OK", "")
            api.change_password("new_password")

            mock_get_data_1.return_value = ("Not OK", "")
            with pytest.raises(
                RuntimeError,
                match="An error occurred when changing AWS Cognito password: Not OK",
            ):
                api.change_password("new_password")

            mock_get_data_1.return_value = ("OK", "")
            mock_get_data_2.return_value = ("Not OK", "")
            with pytest.raises(
                RuntimeError,
                match="An error occurred when changing Hitachi password: Not OK",
            ):
                api.change_password("new_password")

    def test_get_status(self, fixture_aws_mock_api):
        # Test status
        api = fixture_aws_mock_api
        statuses = api.get_status()
        assert isinstance(statuses[MOCK_DEVICE_AC], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_AC].FanSpeed == "high"
        assert statuses[MOCK_DEVICE_AC].status == {
            "DeviceType": "AC",
            "FanSpeed": "high",
            "TemperatureSetting": 26,
            "max_temp": 32,
            "min_temp": 16,
        }
        assert isinstance(statuses[MOCK_DEVICE_DH], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_DH].Mode == "air_purify"
        assert statuses[MOCK_DEVICE_DH].status == {
            "DeviceType": "DH",
            "Mode": "air_purify",
            "max_humidity": 70,
            "min_humidity": 40,
        }
        assert isinstance(statuses[MOCK_DEVICE_HE], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_HE].BreathMode == "normal"
        assert statuses[MOCK_DEVICE_HE].status == {
            "DeviceType": "HE",
            "BreathMode": "normal",
        }

        # Test legacy status
        statuses = api.get_status(legacy=True)
        assert isinstance(statuses[MOCK_DEVICE_AC], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_AC].air_speed == "high"
        assert statuses[MOCK_DEVICE_AC].status == {
            "DeviceType": "AC",
            "air_speed": "high",
            "target_temp": 26,
            "max_temp": 32,
            "min_temp": 16,
        }
        assert isinstance(statuses[MOCK_DEVICE_DH], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_DH].mode == "air_purify"
        assert statuses[MOCK_DEVICE_DH].status == {
            "DeviceType": "DH",
            "mode": "air_purify",
            "max_humidity": 70,
            "min_humidity": 40,
        }
        assert isinstance(statuses[MOCK_DEVICE_HE], JciHitachiAWSStatus)
        assert statuses[MOCK_DEVICE_HE].BreathMode == "normal"
        assert statuses[MOCK_DEVICE_HE].status == {
            "DeviceType": "HE",
            "BreathMode": "normal",
        }

        # Test not existing thing
        statuses = api.get_status("NON_EXISTING_NAME")
        assert statuses == {}

        # Test unknown device type
        with patch.object(api._things[MOCK_DEVICE_AC], "_json") as mock_thing_json:
            mock_thing_json["DeviceType"] = "NON_EXISTING_TYPE"
            statuses = api.get_status(MOCK_DEVICE_AC)
            assert statuses == {}

    def test_refresh_status(self, fixture_aws_mock_api, fixture_aws_identity):
        api = fixture_aws_mock_api
        api._aws_identity = fixture_aws_identity

        thing_name = api.things[MOCK_DEVICE_AC].thing_name
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_mqtt.publish.return_value = None
            mock_mqtt.execute.return_value = [
                [thing_name],
                [thing_name],
                [thing_name],
                [],
            ]
            mock_mqtt.mqtt_events.mqtt_error_event.is_set.return_value = False

            mock_mqtt.mqtt_events.device_status = {thing_name: ""}
            mock_mqtt.mqtt_events.device_support = {thing_name: ""}
            mock_mqtt.mqtt_events.device_shadow = {thing_name: ""}
            api.refresh_status(
                MOCK_DEVICE_AC, refresh_support_code=True, refresh_shadow=True
            )

            # status event timeout
            mock_mqtt.execute.return_value = [
                [thing_name],
                [thing_name],
                [BaseException],
                [],
            ]
            with pytest.raises(
                RuntimeError,
                match=f"Timed out refreshing {MOCK_DEVICE_AC} status code. Please ensure the device is online and avoid opening the official app.",
            ):
                api.refresh_status(MOCK_DEVICE_AC)

            # status not stored in dict
            mock_mqtt.execute.return_value = [
                [thing_name],
                [thing_name],
                [thing_name],
                [],
            ]
            mock_mqtt.mqtt_events.device_status = {}
            with pytest.raises(
                RuntimeError,
                match=f"An event occurred but wasn't accompanied with data when refreshing {MOCK_DEVICE_AC} status code.",
            ):
                api.refresh_status(MOCK_DEVICE_AC)

            # support event timeout
            mock_mqtt.execute.return_value = [
                [BaseException],
                [thing_name],
                [thing_name],
                [],
            ]
            with pytest.raises(
                RuntimeError,
                match=f"Timed out refreshing {MOCK_DEVICE_AC} support code. Please ensure the device is online and avoid opening the official app.",
            ):
                api.refresh_status(MOCK_DEVICE_AC, refresh_support_code=True)

            # support not stored in dict
            mock_mqtt.execute.return_value = [
                [thing_name],
                [thing_name],
                [thing_name],
                [],
            ]
            mock_mqtt.mqtt_events.device_support = {}
            with pytest.raises(
                RuntimeError,
                match=f"An event occurred but wasn't accompanied with data when refreshing {MOCK_DEVICE_AC} support code.",
            ):
                api.refresh_status(MOCK_DEVICE_AC, refresh_support_code=True)

            # shadow event timeout
            mock_mqtt.execute.return_value = [
                [thing_name],
                [BaseException],
                [thing_name],
                [],
            ]
            with pytest.raises(
                RuntimeError,
                match=f"Timed out refreshing {MOCK_DEVICE_AC} shadow. Please ensure the device is online and avoid opening the official app.",
            ):
                api.refresh_status(MOCK_DEVICE_AC, refresh_shadow=True)

            # shadow not stored in dict
            mock_mqtt.execute.return_value = [
                [thing_name],
                [thing_name],
                [thing_name],
                [],
            ]
            mock_mqtt.mqtt_events.device_shadow = {}
            with pytest.raises(
                RuntimeError,
                match=f"An event occurred but wasn't accompanied with data when refreshing {MOCK_DEVICE_AC} shadow.",
            ):
                api.refresh_status(MOCK_DEVICE_AC, refresh_shadow=True)

    def test_set_status(self, fixture_aws_mock_api, fixture_aws_identity):
        api = fixture_aws_mock_api
        api._aws_identity = fixture_aws_identity

        thing_name = api.things[MOCK_DEVICE_AC].thing_name
        with patch.object(api, "_mqtt") as mock_mqtt:
            mock_mqtt.publish.return_value = None
            mock_mqtt.execute.return_value = [[], [], [], [thing_name]]
            mock_mqtt.mqtt_events.mqtt_error_event.is_set.return_value = False
            mock_mqtt.mqtt_events.device_control.get.return_value = {"FanSpeed": 3}

            assert api.set_status(
                "FanSpeed", device_name=MOCK_DEVICE_AC, status_value=3
            )
            assert api.things[MOCK_DEVICE_AC].status_code.FanSpeed == "moderate"

            # Test legacy name
            assert api.set_status(
                "air_speed", device_name=MOCK_DEVICE_AC, status_value=3
            )
            # Test invalid status_name
            assert not api.set_status(
                "invalid", device_name=MOCK_DEVICE_AC, status_value=3
            )
            # Test invalid status_value
            assert not api.set_status(
                "FanSpeed", device_name=MOCK_DEVICE_AC, status_value=8
            )
            # Test status_str_value
            assert api.set_status(
                "FanSpeed", device_name=MOCK_DEVICE_AC, status_str_value="moderate"
            )
            # Test invalid status_str_value
            assert not api.set_status(
                "FanSpeed", device_name=MOCK_DEVICE_AC, status_str_value="invalid"
            )

            mock_mqtt.mqtt_events.device_control_event.wait.return_value = False
            assert not api.set_status(
                "target_temp", device_name=MOCK_DEVICE_AC, status_value=25
            )

    def test_refresh_monthly_data(self, fixture_aws_mock_api):
        api = fixture_aws_mock_api
        with patch(
            "JciHitachi.aws_connection.GetAvailableAggregationMonthlyData.get_data"
        ) as mock_get_data:
            current_time = time.time()
            mock_get_data.return_value = (
                "OK",
                {
                    "results": {
                        "Data": [
                            {"Timestamp": current_time + 300},
                            {"Timestamp": current_time},
                        ]
                    }
                },
            )

            assert api.things[MOCK_DEVICE_AC].monthly_data is None
            api.refresh_monthly_data(2, MOCK_DEVICE_AC)
            assert api.things[MOCK_DEVICE_AC].monthly_data == [
                {"Timestamp": current_time},
                {"Timestamp": current_time + 300},
            ]

            mock_get_data.return_value = ("Not OK", {})

            with pytest.raises(
                RuntimeError,
                match="An error occurred when getting monthly data: Not OK",
            ):
                api.refresh_monthly_data(2, MOCK_DEVICE_AC)


class TestAWSThing:
    def test_repr(
        self,
        fixture_aws_mock_ac_thing,
        fixture_aws_mock_dh_thing,
        fixture_aws_mock_he_thing,
    ):
        ac_thing = fixture_aws_mock_ac_thing
        assert (
            ac_thing.__repr__()
            == f"""name: {MOCK_DEVICE_AC}
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
        )

        dh_thing = fixture_aws_mock_dh_thing
        assert (
            dh_thing.__repr__()
            == f"""name: {MOCK_DEVICE_DH}
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
        )

        he_thing = fixture_aws_mock_he_thing
        assert (
            he_thing.__repr__()
            == f"""name: {MOCK_DEVICE_HE}
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
        )

    def test_properties_and_setters(
        self,
        fixture_aws_mock_ac_thing,
        fixture_aws_mock_dh_thing,
        fixture_aws_mock_he_thing,
    ):
        for thing, device_type in (
            (fixture_aws_mock_ac_thing, "AC"),
            (fixture_aws_mock_dh_thing, "DH"),
            (fixture_aws_mock_he_thing, "HE"),
        ):
            # by default (with a setter)
            assert thing.available == True
            assert thing.shadow == None
            assert thing.status_code.DeviceType == device_type
            assert thing.support_code.DeviceType == device_type
            assert thing.monthly_data == None

            # by default (with no setter)
            assert thing.picked_thing == thing._json

            mock_device_types = {
                "AC": ("DH", 2),
                "DH": ("AC", 1),
                "HE": ("AC", 1),
            }

            # assign new values
            thing.available = False
            thing.shadow = {}
            new_status_code = JciHitachiAWSStatus(
                {
                    "DeviceType": mock_device_types[device_type][1],  # mock unknown
                }
            )
            thing.status_code = new_status_code
            new_support_code = thing.support_code = JciHitachiAWSStatusSupport(
                {
                    "DeviceType": mock_device_types[device_type][1],  # mock unknown
                }
            )
            thing.support_code = new_support_code
            thing.monthly_data = [{}]

            # test new values
            assert thing.available == False
            assert thing.shadow == {}
            assert thing.status_code.DeviceType == mock_device_types[device_type][0]
            assert thing.support_code.DeviceType == mock_device_types[device_type][0]
            assert thing.monthly_data == [{}]

    def test_from_device_names(self):
        things = AWSThing.from_device_names(MOCK_THINGS_JSON, None)
        assert len(things) == 2

        # test specifying device
        things = AWSThing.from_device_names(MOCK_THINGS_JSON, MOCK_DEVICE_AC)
        assert len(things) == 1
        assert things[MOCK_DEVICE_AC].name == MOCK_DEVICE_AC

        # test device name unavailable
        with pytest.raises(
            AssertionError, match="Some of device_names are not available from the API."
        ):
            things = AWSThing.from_device_names(MOCK_THINGS_JSON, "unknown")
