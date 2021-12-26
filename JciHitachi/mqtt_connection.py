import json
import logging
import os
import ssl
import threading
from dataclasses import dataclass, field
from typing import Dict

import paho.mqtt.client as mqtt

from .utility import convert_hash

MQTT_ENDPOINT = "mqtt.jci-hitachi-smarthome.com"
MQTT_PORT = 8893
MQTT_VERSION = 4
MQTT_SSL_CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert/mqtt-jci-hitachi-smarthome-com-chain.pem")
MQTT_SSL_CONTEXT = ssl.create_default_context(cafile=MQTT_SSL_CERT)
MQTT_SSL_CONTEXT.set_ciphers("DEFAULT@SECLEVEL=1")  # the cert uses SHA1-RSA1024bits ciphers so unfortunately we have to lower the security level
MQTT_SSL_CONTEXT.hostname_checks_common_name = True  # the cert lacks a subjectaltname

_LOGGER = logging.getLogger(__name__)


@dataclass
class JciHitachiMqttEvents:
    device_access_time: Dict[str, int] = field(default_factory=dict)
    job: threading.Event = field(default_factory=threading.Event)
    job_done_report: threading.Event = field(default_factory=threading.Event)
    peripheral: threading.Event = field(default_factory=threading.Event)


class JciHitachiMqttConnection:
    """Connecting to Jci-Hitachi MQTT to get latest events.

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    user_id : int
        User ID.
    print_response : bool, optional
        If set, all responses of MQTT will be printed, by default False.
    """

    def __init__(self, email, password, user_id, print_response=False):
        self._email = email
        self._password = password
        self._user_id = user_id
        self._print_response = print_response
        
        self._mqttc = mqtt.Client()
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

    def _on_connect(self, client, userdata, flags, rc):
        if self._print_response:
            print(f"Mqtt connected with result code {rc}")

        client.subscribe(f"out/ugroup/{self._user_id}/#")
    
    def _on_disconnect(self, client, userdata, rc):
        if self._print_response:
            print(f"Mqtt disconnected with result code {rc}")
        
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self._mqttc.loop_stop()
        else:
            _LOGGER.error(f"Unexpected MQTT disconnection: {mqtt.error_string(rc)}.")

    def _on_message(self, client, userdata, msg):
        if self._print_response:
            print(f"{msg.topic} {str(msg.payload)}")
        
        splitted_topic = msg.topic.split('/')
        payload = json.loads(msg.payload)
        if len(splitted_topic) == 6 and splitted_topic[-1] == "status":
            gateway_id = payload["args"]["ObjectID"]
            time = payload["time"]
            self._mqtt_events.device_access_time[gateway_id] = time
        elif len(splitted_topic) == 4 and splitted_topic[-1] == "resp":
            if payload["args"]["Name"] == "JobDoneReport":
                self._mqtt_events.job_done_report.set()
            elif payload["args"]["Name"] == "Peripheral":
                self._mqtt_events.peripheral.set()
        elif len(splitted_topic) == 4 and splitted_topic[-1] == "job":
            if payload["args"]["Name"] == "Job":
                self._mqtt_events.job.set()

    def configure(self):
        """Configure MQTT.
        """

        self._mqttc.username_pw_set(f"$MAIL${self._email}", f"{self._email}{convert_hash(f'{self._email}{self._password}')}")
        self._mqttc.tls_set_context(MQTT_SSL_CONTEXT)
        self._mqttc.on_connect = self._on_connect
        self._mqttc.on_disconnect = self._on_disconnect
        self._mqttc.on_message = self._on_message

        if self._print_response:
            self._mqttc.enable_logger(logger=_LOGGER)

    def connect(self):
        """Connect to the MQTT broker and start loop.
        """

        self._mqttc.connect_async(MQTT_ENDPOINT, port=MQTT_PORT, keepalive=60, bind_address="")
        self._mqttc.loop_start()

    def disconnect(self):
        """Disconnect from the MQTT broker.
        """

        self._mqttc.disconnect()