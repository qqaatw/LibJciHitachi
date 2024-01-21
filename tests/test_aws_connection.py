import concurrent
import datetime
import time
import threading
from unittest.mock import MagicMock, patch

import awscrt
import awsiot
import pytest

from JciHitachi.aws_connection import (
    AWS_COGNITO_ENDPOINT,
    AWS_COGNITO_IDP_ENDPOINT,
    AWS_IOT_ENDPOINT,
    AWSIdentity,
    AWSTokens,
    ChangePassword,
    GetAllDevice,
    GetAllGroup,
    GetAllRegion,
    GetAvailableAggregationMonthlyData,
    GetCredentials,
    GetHistoryEventByUser,
    GetUser,
    JciHitachiAWSCognitoConnection,
    JciHitachiAWSMqttConnection,
    ListSubUser,
)
from JciHitachi.model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

from . import MOCK_GATEWAY_MAC


@pytest.fixture()
def fixture_aws_tokens():
    return AWSTokens("access_token", "id_token", "refresh_token", time.time() + 3600)


@pytest.fixture()
def fixture_aws_mock_mqtt_connection():
    def get_credentials_callable():
        return awscrt.auth.AwsCredentials(
            access_key_id="",
            secret_access_key="",
            session_token="",
            expiration=datetime.datetime.fromtimestamp(time.time()),
        )

    mqtt_connection = JciHitachiAWSMqttConnection(
        get_credentials_callable, print_response=True
    )
    return mqtt_connection


class TestJciHitachiAWSMqttConnection:
    def test_on_publish_callback(self, fixture_aws_mock_mqtt_connection):
        mqtt = fixture_aws_mock_mqtt_connection
        thing_name = (
            f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}"
        )

        status_topic = f"{thing_name.split('_')[0]}/{thing_name}/status/response"
        mqtt._mqtt_events.device_status_event[thing_name] = threading.Event()
        mqtt._on_publish(status_topic, b'{"DeviceType": 1}', None, None, None)
        assert isinstance(
            mqtt._mqtt_events.device_status[thing_name], JciHitachiAWSStatus
        )
        assert mqtt._mqtt_events.device_status_event[thing_name].is_set()

        registration_topic = (
            f"{thing_name.split('_')[0]}/{thing_name}/registration/response"
        )
        mqtt._mqtt_events.device_support_event[thing_name] = threading.Event()
        mqtt._on_publish(registration_topic, b'{"DeviceType": 1}', None, None, None)
        assert isinstance(
            mqtt._mqtt_events.device_support[thing_name], JciHitachiAWSStatusSupport
        )
        assert mqtt._mqtt_events.device_support_event[thing_name].is_set()

        control_topic = f"{thing_name.split('_')[0]}/{thing_name}/control/response"
        mqtt._mqtt_events.device_control_event[thing_name] = threading.Event()
        mqtt._on_publish(control_topic, b'{"DeviceType": 1}', None, None, None)
        assert isinstance(mqtt._mqtt_events.device_control[thing_name], dict)
        assert mqtt._mqtt_events.device_control_event[thing_name].is_set()

        mqtt._mqtt_events.mqtt_error_event.clear()
        mqtt._on_publish("", b"", None, None, None)
        assert mqtt._mqtt_events.mqtt_error == "JSONDecodeError"
        assert mqtt._mqtt_events.mqtt_error_event.is_set()

    def test_on_get_named_shadow_accepted_callback(
        self, fixture_aws_mock_mqtt_connection
    ):
        mqtt = fixture_aws_mock_mqtt_connection
        thing_name = (
            f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}"
        )
        client_token = thing_name.split("_")[1]
        mqtt._client_tokens = {client_token: thing_name}

        response = MagicMock()
        response.client_token = client_token
        response.state.reported = {"Something": 0}
        mqtt._mqtt_events.device_shadow_event[thing_name] = threading.Event()
        mqtt._on_get_named_shadow_accepted(response)
        assert len(mqtt._client_tokens) == 0
        assert isinstance(mqtt._mqtt_events.device_shadow[thing_name], dict)
        assert mqtt._mqtt_events.device_shadow_event[thing_name].is_set()

        response.client_token = ""
        mqtt._on_get_named_shadow_accepted(response)

    def test_on_update_named_shadow_accepted_callback(
        self, fixture_aws_mock_mqtt_connection
    ):
        mqtt = fixture_aws_mock_mqtt_connection
        thing_name = (
            f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}"
        )
        client_token = thing_name.split("_")[1]
        mqtt._client_tokens = {client_token: thing_name}

        response = MagicMock()
        response.client_token = client_token
        response.state.reported = {"Something": 0}
        mqtt._mqtt_events.device_control_event[thing_name] = threading.Event()
        mqtt._on_update_named_shadow_accepted(response)
        assert len(mqtt._client_tokens) == 0
        assert isinstance(mqtt._mqtt_events.device_control[thing_name], dict)
        assert mqtt._mqtt_events.device_control_event[thing_name].is_set()

        response.client_token = ""
        mqtt._on_update_named_shadow_accepted(response)

    def test_configure(self, fixture_aws_mock_mqtt_connection):
        mqtt = fixture_aws_mock_mqtt_connection

        assert mqtt._mqttc is None
        assert mqtt._shadow_mqttc is None

        mqtt.configure(identity_id="identity_id")

        assert isinstance(mqtt._mqttc, awscrt.mqtt.Connection)
        assert isinstance(mqtt._shadow_mqttc, awsiot.iotshadow.IotShadowClient)

    def test_connect(self, fixture_aws_mock_mqtt_connection):
        mqtt = fixture_aws_mock_mqtt_connection

        with patch.object(mqtt, "_mqttc") as mock_mqttc:
            connect_future = concurrent.futures.Future()
            connect_future.set_result(None)
            mock_mqttc.connect.return_value = connect_future
            subscribe_future = concurrent.futures.Future()
            subscribe_future.set_result(None)
            mock_mqttc.subscribe.return_value = (subscribe_future, None)
            assert mqtt.connect("")

        with patch.object(mqtt, "_mqttc") as mock_mqttc:
            connect_future = concurrent.futures.Future()
            connect_future.set_exception(ValueError())
            mock_mqttc.connect.return_value = connect_future
            mqtt._mqtt_events.mqtt_error = ""
            mqtt._mqtt_events.mqtt_error_event.clear()
            assert not mqtt.connect("")
            assert mqtt._mqtt_events.mqtt_error == "ValueError"
            assert mqtt._mqtt_events.mqtt_error_event.is_set()

        with patch.object(mqtt, "_mqttc") as mock_mqttc:
            subscribe_future = concurrent.futures.Future()
            subscribe_future.set_exception(RuntimeError())
            mock_mqttc.subscribe.return_value = (subscribe_future, None)
            mqtt._mqtt_events.mqtt_error = ""
            mqtt._mqtt_events.mqtt_error_event.clear()
            assert not mqtt.connect("")
            assert mqtt._mqtt_events.mqtt_error == "RuntimeError"
            assert mqtt._mqtt_events.mqtt_error_event.is_set()

    def test_publish(self, fixture_aws_mock_mqtt_connection):
        mqtt = fixture_aws_mock_mqtt_connection
        thing_name = (
            f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}"
        )

        assert thing_name not in mqtt._mqtt_events.device_support_event
        with patch.object(mqtt, "_mqttc") as mock_mqttc:
            publish_future = concurrent.futures.Future()
            publish_future.set_result(None)
            mock_mqttc.publish.return_value = (publish_future, None)
            mqtt.publish("", thing_name, "support")
            assert thing_name in mqtt._mqtt_events.device_support_event
            assert len(mqtt._execution_pools.support_execution_pool) == 1

        # test clearing event
        mqtt._mqtt_events.device_support_event[thing_name] = threading.Event()
        mqtt._mqtt_events.device_support_event[thing_name].set()
        with patch.object(mqtt, "_mqttc") as mock_mqttc:
            publish_future = concurrent.futures.Future()
            publish_future.set_result(None)
            mock_mqttc.publish.return_value = (publish_future, None)
            mqtt.publish("", thing_name, "support")
            assert thing_name in mqtt._mqtt_events.device_support_event
            assert not mqtt._mqtt_events.device_support_event[thing_name].is_set()

        # test invalid publish_type
        with patch.object(mqtt, "_mqttc") as mock_mqttc:
            publish_future = concurrent.futures.Future()
            publish_future.set_exception(ValueError())
            mock_mqttc.publish.return_value = (publish_future, None)
            with pytest.raises(ValueError, match="Invalid publish_type: others"):
                mqtt.publish("", thing_name, "others")

        # TODO: test timeout

    @pytest.mark.parametrize("raise_exception", [False, True])
    def test_publish_shadow(self, fixture_aws_mock_mqtt_connection, raise_exception):
        mqtt = fixture_aws_mock_mqtt_connection
        thing_name = (
            f"ap-northeast-1:8916b515-8394-4ccd-95b8-4f553c13dafa_{MOCK_GATEWAY_MAC}"
        )

        with patch.object(mqtt, "_shadow_mqttc") as mock_shadow_mqttc:

            def publish_shadow_func(request, qos):
                assert isinstance(request, awsiot.ModeledClass)
                assert isinstance(qos, int)
                publish_future = concurrent.futures.Future()
                if raise_exception:
                    publish_future.set_exception(RuntimeError())
                else:
                    publish_future.set_result(None)
                return publish_future

            shadow_types_to_test = [
                (mock_shadow_mqttc.publish_get_shadow, "get", None),
                (mock_shadow_mqttc.publish_update_shadow, "update", None),
                (mock_shadow_mqttc.publish_get_named_shadow, "get", "info"),
                (mock_shadow_mqttc.publish_update_named_shadow, "update", "info"),
            ]

            for shadow_func, command_name, shadow_name in shadow_types_to_test:
                shadow_func.side_effect = publish_shadow_func

                mqtt._mqtt_events.mqtt_error = ""
                mqtt._mqtt_events.mqtt_error_event.clear()
                if raise_exception:
                    pass
                    # mqtt.publish_shadow(thing_name, command_name, shadow_name=shadow_name)
                    # assert mqtt._mqtt_events.mqtt_error == "RuntimeError"
                    # assert mqtt._mqtt_events.mqtt_error_event.is_set()
                else:
                    mqtt.publish_shadow(
                        thing_name, command_name, shadow_name=shadow_name
                    )
                    assert not mqtt._mqtt_events.mqtt_error_event.is_set()

        # Test invalid command name.
        with pytest.raises(
            ValueError, match="command_name must be one of `get` or `update`."
        ):
            mqtt.publish_shadow(thing_name, "delete")

    def test_execute(self, fixture_aws_mock_mqtt_connection):
        mqtt = fixture_aws_mock_mqtt_connection
        # The executed functions are no-op.
        mqtt._execution_pools.support_execution_pool.append(
            mqtt._wrap_async("support_identifier", lambda: None)
        )
        mqtt._execution_pools.shadow_execution_pool.append(
            mqtt._wrap_async("shadow_identifier", lambda: None)
        )
        mqtt._execution_pools.status_execution_pool.append(
            mqtt._wrap_async("status_identifier", lambda: None)
        )
        mqtt._execution_pools.control_execution_pool.append(
            mqtt._wrap_async("control_identifier", lambda: None)
        )

        results = mqtt.execute()
        assert results == (
            ["support_identifier"],
            ["shadow_identifier"],
            ["status_identifier"],
            None,
        )
        assert len(mqtt._execution_pools.support_execution_pool) == 0
        assert len(mqtt._execution_pools.shadow_execution_pool) == 0
        assert len(mqtt._execution_pools.status_execution_pool) == 0

        results = mqtt.execute(control=True)
        assert results == (None, None, None, ["control_identifier"])
        assert len(mqtt._execution_pools.control_execution_pool) == 0


class TestJciHitachiAWSCognitoConnection:
    # (class name, get data args, header_target, response json, response type)
    classes_to_test = [
        (
            JciHitachiAWSCognitoConnection,
            None,
            "AWSCognitoIdentityProviderService.InitiateAuth",
            {
                "AuthenticationResult": {
                    "AccessToken": "acc_token",
                    "IdToken": "IdToken",
                    "RefreshToken": "RefreshToken",
                    "ExpiresIn": 3600,
                }
            },
            AWSTokens,
        ),
        (
            ChangePassword,
            {"new_password": "x"},
            "AWSCognitoIdentityProviderService.ChangePassword",
            {},
            type(None),
        ),
        (
            GetUser,
            {},
            "AWSCognitoIdentityProviderService.GetUser",
            {
                "Username": "username",
                "UserAttributes": [
                    {
                        "Name": "custom:cognito_identity_id",
                        "Value": "identity_id",
                    },
                    {
                        "Name": "custom:host_identity_id",
                        "Value": "host_identity_id",
                    },
                ],
            },
            AWSIdentity,
        ),
        (
            GetCredentials,
            {"aws_identity": AWSIdentity("", "", "", {})},
            "AWSCognitoIdentityService.GetCredentialsForIdentity",
            {
                "Credentials": {
                    "AccessKeyId": "acc",
                    "SecretKey": "sec",
                    "SessionToken": "ses",
                    "Expiration": time.time(),
                }
            },
            awscrt.auth.AwsCredentials,
        ),
    ]
    error_response_json = {
        # For invalid requests
        "__type": "NotAuthorizedException",
        "message": "Incorrect username or password.",
    }
    login_response_json = {
        # For login
        "AuthenticationResult": {
            "AccessToken": "abc",
            "IdToken": "def",
            "RefreshToken": "ghi",
            "ExpiresIn": 3600,
        },
    }

    @pytest.mark.parametrize("test_class", classes_to_test)
    def test_get_data_or_login(self, test_class):
        (
            test_class,
            get_data_args,
            header_target,
            response_json,
            response_type,
        ) = test_class
        c = test_class(
            "abc@abc.com",
            "password",
            aws_tokens=AWSTokens("", "", "", time.time()),
            print_response=True,
        )
        with patch("httpx.post") as mock_post:
            response_code = [
                # (code, message)
                (200, "OK"),
                (
                    400,
                    f"{self.error_response_json['__type']} {self.error_response_json['message']}",
                ),
            ]

            for http_status_code, msg in response_code:

                def mock_post_func(
                    endpoint, headers=None, json=None, proxies=None, **kwargs
                ):
                    if isinstance(c, GetCredentials):
                        assert endpoint == f"https://{AWS_COGNITO_ENDPOINT}/"
                    else:
                        assert endpoint == f"https://{AWS_COGNITO_IDP_ENDPOINT}/"
                    assert headers == {
                        "X-Amz-Target": header_target,
                        "User-Agent": "Dalvik/2.1.0",
                        "content-type": "application/x-amz-json-1.1",
                        "Accept": "application/json",
                    }

                    response = MagicMock()
                    response.headers = ""
                    response.status_code = http_status_code
                    if http_status_code == 200:
                        response.json.return_value = response_json
                    else:
                        response.json.return_value = self.error_response_json
                    return response

                mock_post.side_effect = mock_post_func
                if c.__class__.__name__ == "JciHitachiAWSCognitoConnection":
                    response_msg, response = c.login()
                    with pytest.raises(NotImplementedError):
                        c.get_data()
                else:
                    response_msg, response = c.get_data(**get_data_args)

                if http_status_code == 200:
                    assert response_msg == msg
                    assert isinstance(response, response_type)
                else:
                    assert response_msg == msg
                    assert response is None


class TestJciHitachiIoTConnection:
    # (class name, get data args)
    classes_to_test = [
        (GetAllDevice, {}),
        (GetAllGroup, {}),
        (GetAllRegion, {}),
        (
            GetAvailableAggregationMonthlyData,
            {"thing_name": "", "time_start": "", "time_end": ""},
        ),
        (GetHistoryEventByUser, {"time_start": "", "time_end": ""}),
        (ListSubUser, {}),
    ]
    no_need_access_token = ["GetAllDevice", "GetAllRegion"]

    @pytest.mark.parametrize("test_class", classes_to_test)
    def test_generate_headers(self, test_class, fixture_aws_tokens):
        test_class, get_data_args = test_class
        c = test_class(fixture_aws_tokens, print_response=True)

        headers = {
            "authorization": f"Bearer {fixture_aws_tokens.id_token}",
            "User-Agent": "Dalvik/2.1.0",
            "content-type": "application/json",
            "Accept": "application/json",
        }

        if test_class.__name__ not in self.no_need_access_token:
            headers["accesstoken"] = f"Bearer {fixture_aws_tokens.access_token}"
            assert c._generate_headers(True) == headers
        else:
            assert c._generate_headers(False) == headers

    @pytest.mark.parametrize("test_class", classes_to_test)
    def test_get_data(self, test_class, fixture_aws_tokens):
        test_class, get_data_args = test_class
        c = test_class(fixture_aws_tokens, print_response=True)
        with patch("httpx.post") as mock_post:
            response_code = [
                # (code, message)
                (0, "OK"),
                (6, "Invalid email or password"),
                (12, "Invalid session token"),
                (100, "Unknown error"),
            ]

            for code, msg in response_code:
                response_json = {"status": {"code": code}}

                for http_status_code in [200, 400]:

                    def mock_post_func(
                        endpoint, headers=None, json=None, proxies=None, **kwargs
                    ):
                        h = {
                            "authorization": f"Bearer {fixture_aws_tokens.id_token}",
                            "User-Agent": "Dalvik/2.1.0",
                            "content-type": "application/json",
                            "Accept": "application/json",
                        }
                        if test_class.__name__ not in self.no_need_access_token:
                            h[
                                "accesstoken"
                            ] = f"Bearer {fixture_aws_tokens.access_token}"
                        assert (
                            endpoint
                            == f"https://{AWS_IOT_ENDPOINT}/{c.__class__.__name__}"
                        )
                        assert headers == h

                        response = MagicMock()
                        response.headers = ""
                        response.status_code = http_status_code
                        response.json = MagicMock(return_value=response_json)
                        return response

                    mock_post.side_effect = mock_post_func

                    if http_status_code == 200:
                        assert c.get_data(**get_data_args) == (msg, response_json)
                    else:
                        assert c.get_data(**get_data_args) == (
                            f"HTTP exception {http_status_code}",
                            response_json,
                        )
