from __future__ import annotations
import asyncio
import datetime
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from random import random, choices
from typing import Callable, Optional, Union

import awscrt
import httpx
from awsiot import iotshadow, mqtt_connection_builder

from .model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

AWS_REGION = "ap-northeast-1"
AWS_COGNITO_IDP_ENDPOINT = f"cognito-idp.{AWS_REGION}.amazonaws.com"
AWS_COGNITO_ENDPOINT = f"cognito-identity.{AWS_REGION}.amazonaws.com"
AWS_COGNITO_CLIENT_ID = "7kfnjsb66ei1qt5s5gjv6j1lp6"
AWS_COGNITO_USERPOOL_ID = f"{AWS_REGION}_aTZeaievK"

# AMAZON_ROOT_CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), './cert/AmazonRootCA1.pem')
AWS_IOT_ENDPOINT = "iot-api.jci-hitachi-smarthome.com"
AWS_MQTT_ENDPOINT = f"a8kcu267h96in-ats.iot.{AWS_REGION}.amazonaws.com"
QOS = awscrt.mqtt.QoS.AT_LEAST_ONCE

_LOGGER = logging.getLogger(__name__)


@dataclass
class AWSTokens:
    access_token: str
    id_token: str
    refresh_token: str
    expiration: float


@dataclass
class AWSIdentity:
    identity_id: str
    host_identity_id: str
    user_name: str
    user_attributes: dict


@dataclass
class JciHitachiMqttEvents:
    device_status: dict[str, JciHitachiAWSStatus] = field(default_factory=dict)
    device_support: dict[str, JciHitachiAWSStatusSupport] = field(default_factory=dict)
    device_control: dict[str, dict] = field(default_factory=dict)
    device_shadow: dict[str, dict] = field(default_factory=dict)
    mqtt_error: str = field(default_factory=str)
    device_status_event: dict[str, threading.Event] = field(default_factory=dict)
    device_support_event: dict[str, threading.Event] = field(default_factory=dict)
    device_control_event: dict[str, threading.Event] = field(default_factory=dict)
    device_shadow_event: dict[str, threading.Event] = field(default_factory=dict)
    mqtt_error_event: threading.Event = field(default_factory=threading.Event)


@dataclass
class JciHitachiExecutionPools:
    status_execution_pool: list = field(default_factory=list)
    shadow_execution_pool: list = field(default_factory=list)
    support_execution_pool: list = field(default_factory=list)
    control_execution_pool: list = field(default_factory=list)


class JciHitachiAWSHttpConnection(ABC):
    """Abstract class for AWS http connections."""

    @abstractmethod
    def __init__(self, print_response: bool):
        self._print_response = print_response

    @abstractmethod
    def _generate_headers(self):
        ...

    @abstractmethod
    def _handle_response(self, response: httpx.Response):
        ...

    @abstractmethod
    def _send(self):
        ...

    def get_data(self):
        raise NotImplementedError

    def maybe_print_http_response(self, response: httpx.Response) -> None:
        if not self._print_response:
            return

        try:
            text = json.dumps(response.json(), indent=True)
        except json.JSONDecodeError:
            text = response.text

        print("===================================================")
        print(self.__class__.__name__, "Response:")
        print("headers:", response.headers)
        print("status_code:", response.status_code)
        print("text:", text)
        print("===================================================")


class JciHitachiAWSCognitoConnection(JciHitachiAWSHttpConnection):
    """Connecting to Jci-Hitachi AWS Cognito API.

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    aws_tokens : AWSTokens, optional
        If aws_tokens is given, it is used by request;
        otherwise, a login procedure is performed to obtain new aws_tokens,
        by default None.
    proxy : str, optional
        Proxy setting. Format:"IP:port", by default None.
    print_response : bool, optional
        If set, all responses of httpx will be printed, by default False.
    """

    def __init__(
        self,
        email: str,
        password: str,
        aws_tokens: Optional[AWSTokens] = None,
        proxy: Optional[str] = None,
        print_response: bool = False,
    ):
        super().__init__(print_response)
        self._login_response = None
        self._email = email
        self._password = password
        self._proxies = {"http": proxy, "https": proxy} if proxy else None

        if aws_tokens:
            self._aws_tokens = aws_tokens
        else:
            conn_status, self._aws_tokens = self.login()
            if conn_status != "OK":
                raise RuntimeError(
                    f"An error occurred when signing into AWS Cognito Service: {conn_status}"
                )

    def _generate_headers(self, target: str) -> dict[str, str]:
        headers = {
            "X-Amz-Target": target,
            "User-Agent": "Dalvik/2.1.0",
            "content-type": "application/x-amz-json-1.1",
            "Accept": "application/json",
        }
        return headers

    def _handle_response(self, response: httpx.Response) -> tuple(str, dict):
        response_json = response.json()

        if response.status_code == httpx.codes.ok:
            return "OK", response_json
        else:
            return (
                f"{response_json['__type']} {response_json['message']}",
                response_json,
            )

    def _send(self, target: str, json_data: Optional[dict] = None):
        headers = self._generate_headers(target)

        req = httpx.post(
            f"https://{AWS_COGNITO_ENDPOINT if self.__class__.__name__ == 'GetCredentials' else AWS_COGNITO_IDP_ENDPOINT}/",
            json=json_data,
            headers=headers,
            proxies=self._proxies,
        )

        self.maybe_print_http_response(req)

        return self._handle_response(req)

    @property
    def aws_tokens(self) -> AWSTokens:
        return self._aws_tokens

    def login(self, use_refresh_token: bool = False) -> tuple(str, AWSTokens):
        """Login API.

        Parameters
        ----------
        use_refresh_token : bool, optional
            Whether or not to use AWSTokens.refresh_token to login.
            If AWSTokens is not provided, fallback to email and password, by default False

        Returns
        -------
        (str, AWSTokens)
            (status, aws tokens).
        """

        # https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html
        if use_refresh_token and self._aws_tokens is not None:
            login_json_data = {
                "AuthFlow": "REFRESH_TOKEN_AUTH",
                "AuthParameters": {
                    "REFRESH_TOKEN": self._aws_tokens.refresh_token,
                },
                "ClientId": AWS_COGNITO_CLIENT_ID,
            }
        else:
            use_refresh_token = False
            login_json_data = {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "USERNAME": self._email,
                    "PASSWORD": self._password,
                },
                "ClientId": AWS_COGNITO_CLIENT_ID,
            }

        login_headers = self._generate_headers(
            "AWSCognitoIdentityProviderService.InitiateAuth"
        )

        login_req = httpx.post(
            f"https://{AWS_COGNITO_IDP_ENDPOINT}/",
            json=login_json_data,
            headers=login_headers,
            proxies=self._proxies,
        )

        self.maybe_print_http_response(login_req)

        status, response = self._handle_response(login_req)

        aws_tokens = None
        if status == "OK":
            auth_result = response["AuthenticationResult"]
            aws_tokens = AWSTokens(
                access_token=auth_result["AccessToken"],
                id_token=auth_result["IdToken"],
                refresh_token=self._aws_tokens.refresh_token
                if use_refresh_token
                else auth_result["RefreshToken"],
                expiration=time.time() + auth_result["ExpiresIn"],
            )
        return status, aws_tokens


class ChangePassword(JciHitachiAWSCognitoConnection):
    """API internal endpoint.
    https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ChangePassword.html

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)

    def get_data(self, new_password):
        json_data = {
            "AccessToken": self._aws_tokens.access_token,
            "PreviousPassword": self._password,
            "ProposedPassword": new_password,
        }

        status, response = self._send(
            "AWSCognitoIdentityProviderService.ChangePassword", json_data
        )

        return status, None


class GetUser(JciHitachiAWSCognitoConnection):
    """API internal endpoint.
    https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_GetUser.html

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)

    def get_data(self):
        json_data = {
            "AccessToken": self._aws_tokens.access_token,
        }

        status, response = self._send(
            "AWSCognitoIdentityProviderService.GetUser", json_data
        )

        aws_identity = None
        if status == "OK":
            user_attributes = {
                attr["Name"]: attr["Value"] for attr in response["UserAttributes"]
            }
            aws_identity = AWSIdentity(
                identity_id=user_attributes["custom:cognito_identity_id"],
                host_identity_id=user_attributes["custom:host_identity_id"],
                user_name=response["Username"],
                user_attributes=user_attributes,
            )
        return status, aws_identity


class GetCredentials(JciHitachiAWSCognitoConnection):
    """API internal endpoint.

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)

    def get_data(self, aws_identity):
        json_data = {
            "IdentityId": aws_identity.identity_id,
            "Logins": {
                f"{AWS_COGNITO_IDP_ENDPOINT}/{AWS_COGNITO_USERPOOL_ID}": self._aws_tokens.id_token,
            },
        }

        status, response = self._send(
            "AWSCognitoIdentityService.GetCredentialsForIdentity", json_data
        )

        aws_credentials = None
        if status == "OK":
            aws_credentials = awscrt.auth.AwsCredentials(
                access_key_id=response["Credentials"]["AccessKeyId"],
                secret_access_key=response["Credentials"]["SecretKey"],
                session_token=response["Credentials"]["SessionToken"],
                expiration=datetime.datetime.fromtimestamp(
                    response["Credentials"]["Expiration"]
                ),
            )
        return status, aws_credentials


class JciHitachiAWSIoTConnection(JciHitachiAWSHttpConnection):
    """Connecting to Jci-Hitachi AWS IoT API.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    proxy : str, optional
        Proxy setting. Format:"IP:port", by default None.
    print_response : bool, optional
        If set, all responses of httpx will be printed, by default False.
    """

    def __init__(
        self,
        aws_tokens: AWSTokens,
        proxy: Optional[str] = None,
        print_response: bool = False,
    ):
        super().__init__(print_response)
        self._aws_tokens = aws_tokens
        self._proxies = {"http": proxy, "https": proxy} if proxy else None

    def _generate_headers(self, need_access_token: bool) -> dict[str, str]:
        headers = {
            "authorization": f"Bearer {self._aws_tokens.id_token}",
            "User-Agent": "Dalvik/2.1.0",
            "content-type": "application/json",
            "Accept": "application/json",
        }
        if need_access_token:
            headers["accesstoken"] = f"Bearer {self._aws_tokens.access_token}"
        return headers

    def _handle_response(self, response: httpx.Response) -> tuple[int, str, dict]:
        response_json = response.json()
        if response.status_code == httpx.codes.ok:
            code = response_json["status"]["code"]
            if code == 0:
                return code, "OK", response_json
            elif code == 6:
                return code, "Invalid email or password", response_json
            elif code == 12:
                return code, "Invalid session token", response_json
            else:
                return code, "Unknown error", response_json
        else:
            return (
                response.status_code,
                f"HTTP exception {response.status_code}",
                response_json,
            )

    def _send(
        self, api_name: str, json: Optional[dict] = None, need_access_token: bool = True
    ) -> tuple[str, dict]:
        req = httpx.post(
            f"https://{AWS_IOT_ENDPOINT}{api_name}",
            headers=self._generate_headers(need_access_token),
            json=json,
            proxies=self._proxies,
        )

        self.maybe_print_http_response(req)

        code, message, response_json = self._handle_response(req)

        return message, response_json


class GetAllDevice(JciHitachiAWSIoTConnection):
    """API internal endpoint.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens: AWSTokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self) -> tuple[str, dict]:
        return self._send("/GetAllDevice", need_access_token=False)


class GetAllGroup(JciHitachiAWSIoTConnection):
    """API internal endpoint.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens: AWSTokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self) -> tuple[str, dict]:
        return self._send("/GetAllGroup")


class GetAllRegion(JciHitachiAWSIoTConnection):
    """API internal endpoint.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens: AWSTokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self) -> tuple[str, dict]:
        return self._send("/GetAllRegion", need_access_token=False)


class GetAvailableAggregationMonthlyData(JciHitachiAWSIoTConnection):
    """API internal endpoint.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens: AWSTokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(
        self, thing_name: str, time_start: int, time_end: int
    ) -> tuple[str, dict]:
        json_data = {
            "ThingName": thing_name,
            "TimeStart": time_start,
            "TimeEnd": time_end,
        }
        return self._send("/GetAvailableAggregationMonthlyData", json_data)


class GetHistoryEventByUser(JciHitachiAWSIoTConnection):
    """API internal endpoint.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens: AWSTokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self, time_start: int, time_end: int) -> tuple[str, dict]:
        json_data = {
            "TimeStart": time_start,
            "TimeEnd": time_end,
        }
        return self._send("/GetHistoryEventByUser", json_data)


class ListSubUser(JciHitachiAWSIoTConnection):
    """API internal endpoint.

    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens: AWSTokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self) -> tuple[str, dict]:
        return self._send("/ListSubUser")


class JciHitachiAWSMqttConnection:
    """Connecting to Jci-Hitachi AWS MQTT to get latest events.

    Parameters
    ----------
    get_credentials_callable : Callable
        Callable which takes no arguments and returns AwsCredentials.
    print_response : bool, optional
        If set, all responses of MQTT will be printed, by default False.
    """

    def __init__(
        self, get_credentials_callable: Callable, print_response: bool = False
    ):
        self._get_credentials_callable: Callable = get_credentials_callable
        self._print_response: bool = print_response

        self._mqttc: Optional[awscrt.mqtt.Connection] = None
        self._shadow_mqttc: Optional[iotshadow.IotShadowClient] = None
        self._client_tokens: dict[str, str] = {}
        self._mqtt_events: JciHitachiMqttEvents = JciHitachiMqttEvents()
        self._execution_lock: threading.Lock = threading.Lock()
        self._execution_pools: JciHitachiExecutionPools = JciHitachiExecutionPools()

    def __del__(self):
        self.disconnect()

    @property
    def mqtt_events(self) -> JciHitachiMqttEvents:
        """MQTT events.

        Returns
        -------
        JciHitachiMqttEvents
            See JciHitachiMqttEvents.
        """

        return self._mqtt_events

    def _on_publish(self, topic: str, payload: bytes, dup, qos, retain, **kwargs):
        try:
            payload = json.loads(payload.decode())
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            _LOGGER.error(
                f"Mqtt topic {topic} published with payload {payload} cannot be decoded: {e}"
            )
            return

        if self._print_response:
            print(f"Mqtt topic {topic} published with payload \n {payload}")

        split_topic = topic.split("/")

        if len(split_topic) >= 4 and split_topic[3] != "shadow":
            thing_name = split_topic[1]
            if split_topic[2] == "status" and split_topic[3] == "response":
                self._mqtt_events.device_status[thing_name] = JciHitachiAWSStatus(
                    payload
                )
                self._mqtt_events.device_status_event[thing_name].set()
            elif split_topic[2] == "registration" and split_topic[3] == "response":
                self._mqtt_events.device_support[
                    thing_name
                ] = JciHitachiAWSStatusSupport(payload)
                self._mqtt_events.device_support_event[thing_name].set()
            elif split_topic[2] == "control" and split_topic[3] == "response":
                self._mqtt_events.device_control[thing_name] = payload
                self._mqtt_events.device_control_event[thing_name].set()

    def _on_update_named_shadow_accepted(self, response):
        try:
            thing_name = self._client_tokens.pop(response.client_token)
        except:
            _LOGGER.error(
                f"An unknown shadow response is received. Client token: {response.client_token}"
            )
            return

        if self._print_response:
            print(f"An `update` shadow response is received: {response.state.reported}")

        if response.state:
            if response.state.reported:
                self._mqtt_events.device_control[thing_name] = response.state.reported
                self._mqtt_events.device_control_event[thing_name].set()

    def _on_update_named_shadow_rejected(self, error):
        _LOGGER.error(
            f"A shadow request {error.client_token} was rejected by the API: {error.code} {error.message}"
        )

    def _on_get_named_shadow_accepted(self, response):
        try:
            thing_name = self._client_tokens.pop(response.client_token)
        except:
            _LOGGER.error(
                f"An unknown shadow response is received. Client token: {response.client_token}"
            )
            return

        if self._print_response:
            print(f"A `get` shadow response is received: {response.state.reported}")

        if response.state:
            if response.state.reported:
                self._mqtt_events.device_shadow[thing_name] = response.state.reported
                self._mqtt_events.device_shadow_event[thing_name].set()

    def _on_get_named_shadow_rejected(self, error):
        _LOGGER.error(
            f"A shadow request {error.client_token} was rejected by the API: {error.code} {error.message}"
        )

    def _on_message(self, topic, payload, dup, qos, retain, **kwargs):
        return

    def _on_connection_interrupted(self, connection, error, **kwargs):
        _LOGGER.error(f"MQTT connection was interrupted with exception {error}")
        self._mqtt_events.mqtt_error = error.__class__.__name__
        self._mqtt_events.mqtt_error_event.set()

    def _on_connection_resumed(
        self, connection, return_code, session_present, **kwargs
    ):
        if session_present:
            _LOGGER.info("MQTT connection was resumed.")
        else:
            _LOGGER.info(
                "MQTT connection was resumed, but the previous session was lost. Resubscribing..."
            )
            resubscribe_future, packet_id = connection.resubscribe_existing_topics()

            def on_resubscribe_complete(resubscribe_future):
                try:
                    resubscribe_results = resubscribe_future.result()
                    assert resubscribe_results["packet_id"] == packet_id
                    for topic, qos in resubscribe_results["topics"]:
                        assert qos is not None
                except Exception as e:
                    _LOGGER.error("Resubscribe failure:", e)

            resubscribe_future.add_done_callback(on_resubscribe_complete)
            _LOGGER.info("Resubscribed successfully.")
        return

    async def _wrap_async(self, identifier: str, fn: Callable) -> str:
        await asyncio.sleep(
            random() / 2
        )  # randomly wait 0~0.5 seconds to prevent messages flooding to the broker.
        await asyncio.to_thread(fn)
        return identifier

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""

        if self._mqttc is not None:
            self._mqttc.disconnect()

    def configure(self, identity_id) -> None:
        """Configure MQTT.

        Parameters
        ----------
        identity_id : str
            Identity ID.
        """

        cred_provider = awscrt.auth.AwsCredentialsProvider.new_delegate(
            self._get_credentials_callable
        )
        event_loop_group = awscrt.io.EventLoopGroup(1)
        host_resolver = awscrt.io.DefaultHostResolver(event_loop_group)
        client_bootstrap = awscrt.io.ClientBootstrap(event_loop_group, host_resolver)
        self._mqttc = mqtt_connection_builder.websockets_with_default_aws_signing(
            AWS_REGION,
            cred_provider,
            client_bootstrap=client_bootstrap,
            endpoint=AWS_MQTT_ENDPOINT,
            client_id=f"{identity_id}_{''.join(choices('abcdef0123456789', k=16))}",  # {identityid}_{64bit_hex}
            on_connection_interrupted=self._on_connection_interrupted,
            on_connection_resumed=self._on_connection_resumed,
        )
        self._mqttc.on_message(self._on_message)
        self._shadow_mqttc = iotshadow.IotShadowClient(self._mqttc)

    def connect(
        self,
        host_identity_id: str,
        shadow_names: Optional[Union[str, list[str]]] = None,
        thing_names: Optional[Union[str, list[str]]] = None,
    ) -> bool:
        """Connect to the MQTT broker and start loop.

        Parameters
        ----------
        host_identity_id : str
            Host identity ID.
        shadow_names : str or list of str, optional
            Names to be subscribed in Shadow, by default None.
        thing_names : str or list of str, optional
            Things to be subscribed in Shadow, by default None.

        Returns
        -------
        bool
            A bool indicating whether the mqtt is successfully connected and subscribed.
        """

        try:
            connect_future = self._mqttc.connect()
            connect_future.result()
            _LOGGER.info("MQTT Connected.")
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            _LOGGER.error("MQTT connection failed with exception {}".format(e))
            return False

        try:
            subscribe_future, _ = self._mqttc.subscribe(
                f"{host_identity_id}/+/+/response", QOS, callback=self._on_publish
            )
            subscribe_future.result()

            if thing_names is not None and shadow_names is not None:
                shadow_names = (
                    [shadow_names] if isinstance(shadow_names, str) else shadow_names
                )
                thing_names = (
                    [thing_names] if isinstance(thing_names, str) else thing_names
                )

                for shadow_name in shadow_names:
                    for thing_name in thing_names:
                        (
                            update_accepted_subscribed_future,
                            _,
                        ) = self._shadow_mqttc.subscribe_to_update_named_shadow_accepted(
                            request=iotshadow.UpdateNamedShadowSubscriptionRequest(
                                shadow_name=shadow_name, thing_name=thing_name
                            ),
                            qos=QOS,
                            callback=self._on_update_named_shadow_accepted,
                        )

                        (
                            update_rejected_subscribed_future,
                            _,
                        ) = self._shadow_mqttc.subscribe_to_update_named_shadow_rejected(
                            request=iotshadow.UpdateNamedShadowSubscriptionRequest(
                                shadow_name=shadow_name, thing_name=thing_name
                            ),
                            qos=QOS,
                            callback=self._on_update_named_shadow_rejected,
                        )

                        # Wait for subscriptions to succeed
                        update_accepted_subscribed_future.result()
                        update_rejected_subscribed_future.result()

                        (
                            get_accepted_subscribed_future,
                            _,
                        ) = self._shadow_mqttc.subscribe_to_get_named_shadow_accepted(
                            request=iotshadow.GetNamedShadowSubscriptionRequest(
                                shadow_name=shadow_name, thing_name=thing_name
                            ),
                            qos=QOS,
                            callback=self._on_get_named_shadow_accepted,
                        )

                        (
                            get_rejected_subscribed_future,
                            _,
                        ) = self._shadow_mqttc.subscribe_to_get_named_shadow_rejected(
                            request=iotshadow.GetNamedShadowSubscriptionRequest(
                                shadow_name=shadow_name, thing_name=thing_name
                            ),
                            qos=QOS,
                            callback=self._on_get_named_shadow_rejected,
                        )

                        # Wait for subscriptions to succeed
                        get_accepted_subscribed_future.result()
                        get_rejected_subscribed_future.result()

        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            self.disconnect()
            _LOGGER.error("MQTT subscription failed with exception {}".format(e))
            return False
        return True

    def publish(
        self,
        host_identity_id: str,
        thing_name: str,
        publish_type: str,
        timeout: float = 10.0,
        payload: Optional[dict] = None,
    ) -> None:
        """Put messages to be published in the execution pool. execute() should be called to start async publish.

        Parameters
        ----------
        host_identity_id : str
            Host identity id.
        thing_name : str
            Thing name.
        publish_type: str
            Publish type. There are three types available: `support`, `status`, and `control`.
        timeout: float, optional
            Timeout for messages published, by default 10.0.
        payload : dict, optional
            Payload to publish, by default None.
        """

        default_payload = {"Timestamp": time.time()}

        if publish_type == "support":
            support_topic = f"{host_identity_id}/{thing_name}/registration/request"
            if thing_name in self._mqtt_events.device_support_event:
                self._mqtt_events.device_support_event[thing_name].clear()
            else:
                self._mqtt_events.device_support_event[thing_name] = threading.Event()

            def fn():
                publish_future, _ = self._mqttc.publish(
                    support_topic, json.dumps(default_payload), QOS
                )
                publish_future.result(timeout)
                self._mqtt_events.device_support_event[thing_name].wait(timeout)

            self._execution_pools.support_execution_pool.append(
                self._wrap_async(thing_name, fn)
            )
        elif publish_type == "status":
            status_topic = f"{host_identity_id}/{thing_name}/status/request"
            if thing_name in self._mqtt_events.device_status_event:
                self._mqtt_events.device_status_event[thing_name].clear()
            else:
                self._mqtt_events.device_status_event[thing_name] = threading.Event()

            def fn():
                publish_future, _ = self._mqttc.publish(
                    status_topic, json.dumps(default_payload), QOS
                )
                publish_future.result(timeout)
                self._mqtt_events.device_status_event[thing_name].wait(timeout)

            self._execution_pools.status_execution_pool.append(
                self._wrap_async(thing_name, fn)
            )
        elif publish_type == "control":
            control_topic = f"{host_identity_id}/{thing_name}/control/request"
            if thing_name in self._mqtt_events.device_control_event:
                self._mqtt_events.device_control_event[thing_name].clear()
            else:
                self._mqtt_events.device_control_event[thing_name] = threading.Event()

            def fn():
                publish_future, _ = self._mqttc.publish(
                    control_topic, json.dumps(payload), QOS
                )
                publish_future.result(timeout)
                self._mqtt_events.device_control_event[thing_name].wait(timeout)

            self._execution_pools.control_execution_pool.append(
                self._wrap_async(thing_name, fn)
            )

        else:
            raise ValueError(f"Invalid publish_type: {publish_type}")

    def publish_shadow(
        self,
        thing_name: str,
        command_name: str,
        payload: dict = {},
        shadow_name: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        """Publish message to IoT Shadow Service.

        Parameters
        ----------
        thing_name : str
            Thing name.
        command_name : str
            Command name, which can be `get` or `update`.
        payload : dict, optional
            Payload to publish, by default {}.
        shadow_name : str, optional
            Shadow name, by default None.
        timeout: float, optional
            Timeout for messages published, by default 10.0.
        """

        if command_name not in ["get", "update"]:  # we don't subscribe delete
            raise ValueError("command_name must be one of `get` or `update`.")

        # The length of client token can't exceed 64 bytes, so we only use gateway mac address as the token.
        client_token = thing_name.split("_")[1]
        self._client_tokens.update({client_token: thing_name})
        if thing_name in self._mqtt_events.device_shadow_event:
            self._mqtt_events.device_shadow_event[thing_name].clear()
        else:
            self._mqtt_events.device_shadow_event[thing_name] = threading.Event()

        def fn():
            if shadow_name is None:
                if command_name == "get":
                    publish_future = self._shadow_mqttc.publish_get_shadow(
                        iotshadow.GetShadowRequest(
                            client_token=client_token, thing_name=thing_name
                        ),
                        qos=QOS,
                    )
                elif command_name == "update":
                    publish_future = self._shadow_mqttc.publish_update_shadow(
                        iotshadow.UpdateShadowRequest(
                            client_token=client_token,
                            state=iotshadow.ShadowState(reported=payload),
                            thing_name=thing_name,
                        ),
                        qos=QOS,
                    )
                elif command_name == "delete":
                    publish_future = self._shadow_mqttc.publish_delete_shadow(
                        iotshadow.DeleteShadowRequest(
                            client_token=client_token, thing_name=thing_name
                        ),
                        qos=QOS,
                    )

            else:
                if command_name == "get":
                    publish_future = self._shadow_mqttc.publish_get_named_shadow(
                        iotshadow.GetNamedShadowRequest(
                            client_token=client_token,
                            shadow_name=shadow_name,
                            thing_name=thing_name,
                        ),
                        qos=QOS,
                    )
                elif command_name == "update":
                    publish_future = self._shadow_mqttc.publish_update_named_shadow(
                        iotshadow.UpdateNamedShadowRequest(
                            client_token=client_token,
                            shadow_name=shadow_name,
                            state=iotshadow.ShadowState(reported=payload),
                            thing_name=thing_name,
                        ),
                        qos=QOS,
                    )
                elif command_name == "delete":
                    publish_future = self._shadow_mqttc.publish_delete_named_shadow(
                        iotshadow.DeleteNamedShadowRequest(
                            client_token=client_token,
                            shadow_name=shadow_name,
                            thing_name=thing_name,
                        ),
                        qos=QOS,
                    )
            publish_future.result(timeout)
            self._mqtt_events.device_shadow_event[thing_name].wait(timeout)

        self._execution_pools.shadow_execution_pool.append(
            self._wrap_async(thing_name, fn)
        )

    def execute(
        self, control: bool = False
    ) -> list[
        list[Union[str, BaseException]],
        list[Union[str, BaseException]],
        list[Union[str, BaseException]],
        list[Union[str, BaseException]],
    ]:
        """Execute publish commands in the execution pools.

        Parameters
        ----------
        control : bool
            If True, commands in the `control_execution_pool` will be executed; otherwise, commands in other execution pools will be executed.

        Returns
        -------
        list
            Execution results of support, shadow, status, control, respectively.
            Each result is a list containing thing names if the execution was successful or BaseException(s) if an error occurred during execution.
        """

        async def runner():
            a, b, c, d = None, None, None, None
            if control and len(self._execution_pools.control_execution_pool) != 0:
                d = await asyncio.gather(
                    *self._execution_pools.control_execution_pool,
                    return_exceptions=True,
                )
                self._execution_pools.control_execution_pool.clear()
            else:
                if len(self._execution_pools.support_execution_pool) != 0:
                    a = await asyncio.gather(
                        *self._execution_pools.support_execution_pool,
                        return_exceptions=True,
                    )
                    self._execution_pools.support_execution_pool.clear()
                if len(self._execution_pools.shadow_execution_pool) != 0:
                    b = await asyncio.gather(
                        *self._execution_pools.shadow_execution_pool,
                        return_exceptions=True,
                    )
                    self._execution_pools.shadow_execution_pool.clear()
                if len(self._execution_pools.status_execution_pool) != 0:
                    c = await asyncio.gather(
                        *self._execution_pools.status_execution_pool,
                        return_exceptions=True,
                    )
                    self._execution_pools.status_execution_pool.clear()

            return a, b, c, d

        locked = self._execution_lock.locked()
        if locked:
            _LOGGER.debug("Other execution in progress, waiting for a lock.")

        with self._execution_lock:
            if locked:
                _LOGGER.debug("Lock acquired.")
            results = asyncio.run(runner())

        return results
