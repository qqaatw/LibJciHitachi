import datetime
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict

import awscrt
import httpx
from awsiot import iotshadow, mqtt_connection_builder

from .model import JciHitachiAWSStatus, JciHitachiAWSStatusSupport

AWS_COGNITO_REGION = "ap-northeast-1"
AWS_COGNITO_IDP_ENDPOINT = f"cognito-idp.{AWS_COGNITO_REGION}.amazonaws.com/"
AWS_COGNITO_ENDPOINT = f"cognito-identity.{AWS_COGNITO_REGION}.amazonaws.com/"
AWS_COGNITO_CLIENT_ID = "7kfnjsb66ei1qt5s5gjv6j1lp6"
AWS_COGNITO_USERPOOL_ID = "ap-northeast-1_aTZeaievK"

#AMAZON_ROOT_CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), './cert/AmazonRootCA1.pem')
AWS_IOT_ENDPOINT = "https://iot-api.jci-hitachi-smarthome.com"
AWS_MQTT_ENDPOINT = "a8kcu267h96in-ats.iot.ap-northeast-1.amazonaws.com"

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
    user_name: str
    user_attributes: dict

@dataclass
class JciHitachiMqttEvents:
    device_status: Dict[str, JciHitachiAWSStatus] = field(default_factory=dict)
    device_support: Dict[str, JciHitachiAWSStatusSupport] = field(default_factory=dict)
    device_control: Dict[str, dict] = field(default_factory=dict)
    device_shadow: Dict[str, dict] = field(default_factory=dict)
    mqtt_error: str = field(default_factory=str)
    device_status_event: threading.Event = field(default_factory=threading.Event)
    device_support_event: threading.Event = field(default_factory=threading.Event)
    device_control_event: threading.Event = field(default_factory=threading.Event)
    device_shadow_event: threading.Event = field(default_factory=threading.Event)
    mqtt_error_event: threading.Event = field(default_factory=threading.Event)


class JciHitachiAWSCognitoConnection:
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
    
    def __init__(self, email, password, aws_tokens=None, proxy=None, print_response=False):
        self._login_response = None
        self._email = email
        self._password = password
        self._print_response = print_response
        self._proxies = {'http': proxy, 'https': proxy} if proxy else None

        if aws_tokens:
            self._aws_tokens = aws_tokens
        else:
            conn_status, self._aws_tokens = self.login()
            if conn_status != "OK":
                raise RuntimeError(f"An error occurred when signing into AWS Cognito Service: {conn_status}")
    
    def _generate_headers(self, target):
        normal_headers = {
            "X-Amz-Target": target,
            "User-Agent": "Dalvik/2.1.0",
            "content-type": "application/x-amz-json-1.1",
            "Accept" : "application/json",
        }
        return normal_headers

    def _handle_response(self, response):
        response_json = response.json()
        
        if response.status_code == httpx.codes.ok:    
            return "OK", response_json
        else:
            return f"{response_json['__type']} {response_json['message']}", response_json

    @property
    def aws_tokens(self):
        return self._aws_tokens

    def login(self, use_refresh_token=False):
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
        if use_refresh_token and self._aws_tokens != None:
            login_json_data = {
                "AuthFlow": 'REFRESH_TOKEN_AUTH',
                "AuthParameters":{
                    'REFRESH_TOKEN': self._aws_tokens.refresh_token,
                },
                "ClientId": AWS_COGNITO_CLIENT_ID,
            }
        else:
            use_refresh_token = False
            login_json_data = {
                "AuthFlow": 'USER_PASSWORD_AUTH',
                "AuthParameters": {
                    'USERNAME': self._email,
                    'PASSWORD': self._password,
                },
                "ClientId": AWS_COGNITO_CLIENT_ID,
            }

        login_headers = self._generate_headers("AWSCognitoIdentityProviderService.InitiateAuth")

        login_req = httpx.post("{}".format(f"https://{AWS_COGNITO_IDP_ENDPOINT}"), 
            json=login_json_data,
            headers=login_headers,
            proxies=self._proxies,
        )

        if self._print_response:
            self.print_response(login_req)

        status, response = self._handle_response(login_req)

        aws_tokens = None
        if status == "OK":        
            auth_result = response["AuthenticationResult"]
            aws_tokens = AWSTokens(
                access_token = auth_result['AccessToken'],
                id_token = auth_result['IdToken'],
                refresh_token = self._aws_tokens.refresh_token if use_refresh_token else auth_result['RefreshToken'],
                expiration = time.time() + auth_result['ExpiresIn'],
            )
        return status, aws_tokens

    def get_data(self):
        raise NotImplementedError

    def print_response(self, response):
        print('===================================================')
        print(self.__class__.__name__, 'Response:')
        print('headers:', response.headers)
        print('status_code:', response.status_code)
        print('text:', json.dumps(response.json(), indent=True))
        print('===================================================')


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

        headers = self._generate_headers("AWSCognitoIdentityProviderService.ChangePassword")

        req = httpx.post("{}".format(f"https://{AWS_COGNITO_IDP_ENDPOINT}"), 
            json=json_data,
            headers=headers,
            proxies=self._proxies,
        )

        if self._print_response:
            self.print_response(req)

        status, response = self._handle_response(req)

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

        headers = self._generate_headers("AWSCognitoIdentityProviderService.GetUser")

        req = httpx.post("{}".format(f"https://{AWS_COGNITO_IDP_ENDPOINT}"), 
            json=json_data,
            headers=headers,
            proxies=self._proxies,
        )

        if self._print_response:
            self.print_response(req)

        status, response = self._handle_response(req)

        aws_identity = None
        if status == "OK":
            user_attributes = {attr["Name"]: attr["Value"] for attr in response["UserAttributes"]}
            aws_identity = AWSIdentity(
                identity_id = user_attributes["custom:cognito_identity_id"],
                user_name = response["Username"],
                user_attributes = user_attributes,
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
                f"{AWS_COGNITO_IDP_ENDPOINT}{AWS_COGNITO_USERPOOL_ID}": self._aws_tokens.id_token,
            }
        }

        headers = self._generate_headers("AWSCognitoIdentityService.GetCredentialsForIdentity")

        req = httpx.post("{}".format(f"https://{AWS_COGNITO_ENDPOINT}"), 
            json=json_data,
            headers=headers,
            proxies=self._proxies,
        )

        if self._print_response:
            self.print_response(req)

        status, response = self._handle_response(req)

        aws_credentials = None
        if status == "OK":
            aws_credentials = awscrt.auth.AwsCredentials(
                access_key_id = response["Credentials"]["AccessKeyId"],
                secret_access_key = response["Credentials"]["SecretKey"],
                session_token = response["Credentials"]["SessionToken"],
                expiration = datetime.datetime.fromtimestamp(response["Credentials"]["Expiration"]),
            )
        return status, aws_credentials


class JciHitachiAWSIoTConnection:
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

    def __init__(self, aws_tokens, proxy=None, print_response=False):
        self._aws_tokens = aws_tokens
        self._print_response = print_response
        self._proxies = {'http': proxy, 'https': proxy} if proxy else None
    
    def _generate_normal_headers(self):
        normal_headers = {
            "authorization": f"Bearer {self._aws_tokens.id_token}",
            "accesstoken": f"Bearer {self._aws_tokens.access_token}",
            "User-Agent": "Dalvik/2.1.0",
            "content-type" : "application/json",
            "Accept" : "application/json",
        }
        return normal_headers

    def _handle_response(self, response):
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
            return response.status_code, f"HTTP exception {response.status_code}", response_json

    def _send(self, api_name, json=None):
        req = httpx.post(
            "{}{}".format(AWS_IOT_ENDPOINT, api_name),
            headers=self._generate_normal_headers(),
            json=json,
            proxies=self._proxies,
        )
        if self._print_response:
            self.print_response(req)

        code, message, response_json = self._handle_response(req)

        return message, response_json

    def get_data(self):
        raise NotImplementedError

    def print_response(self, response):
        print('===================================================')
        print(self.__class__.__name__, 'Response:')
        print('headers:', response.headers)
        print('status_code:', response.status_code)
        print('text:', json.dumps(response.json(), indent=True))
        print('===================================================')


class GetAllDevice(JciHitachiAWSIoTConnection):
    """API internal endpoint.
    
    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self):
        return self._send("/GetAllDevice")


class GetAllGroup(JciHitachiAWSIoTConnection):
    """API internal endpoint.
    
    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self):
        return self._send("/GetAllGroup")


class GetAllRegion(JciHitachiAWSIoTConnection):
    """API internal endpoint.
    
    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self):
        return self._send("/GetAllRegion")


class GetAvailableAggregationMonthlyData(JciHitachiAWSIoTConnection):
    """API internal endpoint.
    
    Parameters
    ----------
    aws_tokens : AWSTokens
        AWS tokens.
    """

    def __init__(self, aws_tokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self, thing_name, time_start, time_end):
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

    def __init__(self, aws_tokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self, time_start, time_end):
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

    def __init__(self, aws_tokens, **kwargs):
        super().__init__(aws_tokens, **kwargs)

    def get_data(self):
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

    def __init__(self, get_credentials_callable, print_response=False):
        self._get_credentials_callable = get_credentials_callable
        self._print_response = print_response
        
        self._mqttc = None
        self._shadow_mqttc = None
        self._client_tokens = {}
        self._mqtt_events = JciHitachiMqttEvents()

    def __del__(self):
        self.disconnect()

    @property
    def mqtt_events(self):
        """MQTT events.

        Returns
        -------
        JciHitachiMqttEvents
            See JciHitachiMqttEvents.
        """

        return self._mqtt_events

    def _on_publish(self, topic, payload, dup, qos, retain, **kwargs):
        try:
            payload = json.loads(payload.decode())
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            _LOGGER.error(f"Mqtt topic {topic} published with payload {payload} cannot be decoded: {e}")
            return

        if self._print_response:
            print(f"Mqtt topic {topic} published with payload \n {payload}")

        split_topic = topic.split('/')

        if len(split_topic) >= 4 and split_topic[3] != "shadow":
            thing_name = split_topic[1]
            if split_topic[2] == "status" and split_topic[3] == "response":
                self._mqtt_events.device_status[thing_name] = JciHitachiAWSStatus(payload)
                self._mqtt_events.device_status_event.set()
            elif split_topic[2] == "registration" and split_topic[3] == "response":
                self._mqtt_events.device_support[thing_name] = JciHitachiAWSStatusSupport(payload)
                self._mqtt_events.device_support_event.set()
            elif split_topic[2] == "control" and split_topic[3] == "response":
                self._mqtt_events.device_control[thing_name] = payload
                self._mqtt_events.device_control_event.set()

    def _on_update_named_shadow_accepted(self, response):
        try:
            thing_name = self._client_tokens.pop(response.client_token)
        except:
            _LOGGER.error(f"An unknown shadow response is received. Client token: {response.client_token}")
            return
        
        if response.state:
            if response.state.reported:
                self._mqtt_events.device_control[thing_name] = response.state.reported
                self._mqtt_events.device_control_event.set()
    
    def _on_update_named_shadow_rejected(self, error):
        _LOGGER.error(f"A shadow request {error.client_token} was rejected by the API: {error.code} {error.message}")

    def _on_get_named_shadow_accepted(self, response):
        try:
            thing_name = self._client_tokens.pop(response.client_token)
        except:
            _LOGGER.error(f"An unknown shadow response is received. Client token: {response.client_token}")
            return

        if response.state:
            if response.state.reported:
                self._mqtt_events.device_shadow[thing_name] = response.state.reported
                self._mqtt_events.device_shadow_event.set()
    
    def _on_get_named_shadow_rejected(self, error):
        _LOGGER.error(f"A shadow request {error.client_token} was rejected by the API: {error.code} {error.message}")

    def _on_message(self, topic, payload, dup, qos, retain, **kwargs):
        return

    def disconnect(self):
        """Disconnect from the MQTT broker.
        """

        if self._mqttc is not None:
            self._mqttc.disconnect()

    def configure(self):
        """Configure MQTT."""

        cred_provider = awscrt.auth.AwsCredentialsProvider.new_delegate(self._get_credentials_callable)
        event_loop_group = awscrt.io.EventLoopGroup(1)
        host_resolver = awscrt.io.DefaultHostResolver(event_loop_group)
        client_bootstrap = awscrt.io.ClientBootstrap(event_loop_group, host_resolver)
        self._mqttc = mqtt_connection_builder.websockets_with_default_aws_signing(
            AWS_COGNITO_REGION,
            cred_provider,
            client_bootstrap=client_bootstrap,
            endpoint=AWS_MQTT_ENDPOINT,
            client_id=str(uuid.uuid4())
        )
        self._mqttc.on_message(self._on_message)
        self._shadow_mqttc = iotshadow.IotShadowClient(self._mqttc)

    def connect(self,  host_identity_id, shadow_names=None, thing_names=None):
        """Connect to the MQTT broker and start loop.
        
        Parameters
        ----------
        host_identity_id : str
            Host identity ID.
        shadow_names : str or list of str, optional
            Names to be subscribed in Shadow, by default None.
        thing_names : str or list of str, optional
            Things to be subscribed in Shadow, by default None.
        """
        
        try:
            connect_future = self._mqttc.connect()
            connect_future.result()
            _LOGGER.info("MQTT Connected.")
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            _LOGGER.error('MQTT connection failed with exception {}'.format(e))
            return False

        try:
            subscribe_future, _ = self._mqttc.subscribe(f"{host_identity_id}/#", awscrt.mqtt.QoS.AT_LEAST_ONCE, callback=self._on_publish)
            subscribe_future.result()
            
            if thing_names is not None and shadow_names is not None:
                shadow_names = [shadow_names] if isinstance(shadow_names, str) else shadow_names
                thing_names = [thing_names] if isinstance(thing_names, str) else thing_names
                
                for shadow_name in shadow_names:
                    for thing_name in thing_names:
                        update_accepted_subscribed_future, _ = self._shadow_mqttc.subscribe_to_update_named_shadow_accepted(
                            request=iotshadow.UpdateNamedShadowSubscriptionRequest(shadow_name=shadow_name, thing_name=thing_name),
                            qos=awscrt.mqtt.QoS.AT_LEAST_ONCE,
                            callback=self._on_update_named_shadow_accepted)

                        update_rejected_subscribed_future, _ = self._shadow_mqttc.subscribe_to_update_named_shadow_rejected(
                            request=iotshadow.UpdateNamedShadowSubscriptionRequest(shadow_name=shadow_name, thing_name=thing_name),
                            qos=awscrt.mqtt.QoS.AT_LEAST_ONCE,
                            callback=self._on_update_named_shadow_rejected)

                        # Wait for subscriptions to succeed
                        update_accepted_subscribed_future.result()
                        update_rejected_subscribed_future.result()

                        get_accepted_subscribed_future, _ = self._shadow_mqttc.subscribe_to_get_named_shadow_accepted(
                            request=iotshadow.GetNamedShadowSubscriptionRequest(shadow_name=shadow_name, thing_name=thing_name),
                            qos=awscrt.mqtt.QoS.AT_LEAST_ONCE,
                            callback=self._on_get_named_shadow_accepted)

                        get_rejected_subscribed_future, _ = self._shadow_mqttc.subscribe_to_get_named_shadow_rejected(
                            request=iotshadow.GetNamedShadowSubscriptionRequest(shadow_name=shadow_name, thing_name=thing_name),
                            qos=awscrt.mqtt.QoS.AT_LEAST_ONCE,
                            callback=self._on_get_named_shadow_rejected)

                        # Wait for subscriptions to succeed
                        get_accepted_subscribed_future.result()
                        get_rejected_subscribed_future.result()
        
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            self.disconnect()
            _LOGGER.error('MQTT subscription failed with exception {}'.format(e))
            return False
        return True

    def publish(self, topic, payload):
        """Publish message.
        
        Parameters
        ----------
        topic : str
            Topic to publish.
        payload : dict
            Payload to publish.
        """

        try:
            publish_future, _ = self._mqttc.publish(topic, json.dumps(payload), awscrt.mqtt.QoS.AT_LEAST_ONCE)
            publish_future.result()
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            _LOGGER.error('Publish failed with exception: {}'.format(e))

    def publish_shadow(self, thing_name, command_name, payload={}, shadow_name=None):
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
        """

        if command_name not in ["get", "update"]: # we don't subscribe delete
            raise ValueError("command_name must be one of `get` or `update`.")

        # The length of client token can't exceed 64 bytes, so we only use gateway mac address as the token.
        client_token = thing_name.split("_")[1] 
        self._client_tokens.update({client_token: thing_name})

        if shadow_name is None:
            if command_name == "get":
                publish_future = self._shadow_mqttc.publish_get_shadow(
                    iotshadow.GetShadowRequest(
                        client_token=client_token,
                        thing_name=thing_name
                    ),
                    qos=awscrt.mqtt.QoS.AT_LEAST_ONCE
                )
            elif command_name == "update":
                publish_future = self._shadow_mqttc.publish_update_shadow(
                    iotshadow.UpdateShadowRequest(
                        client_token=client_token,
                        state=iotshadow.ShadowState(reported=payload),
                        thing_name=thing_name
                    ),
                    qos=awscrt.mqtt.QoS.AT_LEAST_ONCE
                )
            elif command_name == "delete":
                publish_future = self._shadow_mqttc.publish_delete_shadow(
                    iotshadow.DeleteShadowRequest(
                        client_token=client_token,
                        thing_name=thing_name
                    ),
                    qos=awscrt.mqtt.QoS.AT_LEAST_ONCE
                )

        else:
            if command_name == "get":
                publish_future = self._shadow_mqttc.publish_get_named_shadow(
                    iotshadow.GetNamedShadowRequest(
                        client_token=client_token,
                        shadow_name=shadow_name,
                        thing_name=thing_name
                    ),
                    qos=awscrt.mqtt.QoS.AT_LEAST_ONCE
                )
            elif command_name == "update":
                publish_future = self._shadow_mqttc.publish_update_named_shadow(
                    iotshadow.UpdateNamedShadowRequest(
                        client_token=client_token,
                        shadow_name=shadow_name,
                        state=iotshadow.ShadowState(reported=payload),
                        thing_name=thing_name
                    ),
                    qos=awscrt.mqtt.QoS.AT_LEAST_ONCE
                )
            elif command_name == "delete":
                publish_future = self._shadow_mqttc.publish_delete_named_shadow(
                    iotshadow.DeleteNamedShadowRequest(
                        client_token=client_token,
                        shadow_name=shadow_name, 
                        thing_name=thing_name
                    ),
                    qos=awscrt.mqtt.QoS.AT_LEAST_ONCE
                )
        try:
            publish_future.result()
        except Exception as e:
            self._mqtt_events.mqtt_error = e.__class__.__name__
            self._mqtt_events.mqtt_error_event.set()
            _LOGGER.error('Publish failed with exception: {}'.format(e))