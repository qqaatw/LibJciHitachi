import json
import os
import ssl
import threading

import paho.mqtt.client as mqtt

from .utility import convert_hash

MQTT_ENDPOINT = "mqtt.jci-hitachi-smarthome.com"
MQTT_PORT = 8893
MQTT_VERSION = 4
MQTT_SSL_CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cert/mqtt-jci-hitachi-smarthome-com-chain.pem")


class JciHitachiMqttConnection:
    def __init__(self, email, password, user_id, print_response=False):
        self._email = email
        self._password = password
        self._user_id = user_id
        self._print_response = print_response
        
        self._mqttc = mqtt.Client()
        self.wait_job = threading.Event()
        self.wait_job_done_report = threading.Event()
        self.wait_peripheral = threading.Event()
        self._mqtt_event = {
            "device_access_time": {},
            "job": False,
            "job_done_report": False,
        }

    @property
    def mqtt_event(self):
        return self._mqtt_event

    def _on_connect(self, client, userdata, flags, rc):
        if self._print_response:
            print(f"Mqtt connected with result code {rc}")

        client.subscribe(f"out/ugroup/{self._user_id}/#")
    
    def _on_disconnect(self, client, userdata, rc):
        if self._print_response:
            print(f"Mqtt disconnected with result code {rc}")

    def _on_message(self, client, userdata, msg):
        if self._print_response:
            print(f"{msg.topic} {str(msg.payload)}")
        
        splitted_topic = msg.topic.split('/')
        payload = json.loads(msg.payload)
        if len(splitted_topic) == 6 and splitted_topic[-1] == "status":
            gateway_id = payload["args"]["ObjectID"]
            time = payload["time"]
            self._mqtt_event["device_access_time"][gateway_id] = time
        elif len(splitted_topic) == 4 and splitted_topic[-1] == "resp":
            if payload["args"]["Name"] == "JobDoneReport":
                self.wait_job_done_report.set()
            elif payload["args"]["Name"] == "Peripheral":
                self.wait_peripheral.set()
        elif len(splitted_topic) == 4 and splitted_topic[-1] == "job":
            if payload["args"]["Name"] == "Job":
                self.wait_job.set()

    def configure(self):
        self._mqttc.username_pw_set(f"$MAIL${self._email}", f"{self._email}{convert_hash(f'{self._email}{self._password}')}")
        self._mqttc.tls_set(ca_certs=MQTT_SSL_CERT, cert_reqs=ssl.CERT_OPTIONAL)
        self._mqttc.on_connect = self._on_connect
        self._mqttc.on_disconnect = self._on_disconnect
        self._mqttc.on_message = self._on_message

        if self._print_response:
            self._mqttc.enable_logger(logger=None)

    def connect(self):
        self._mqttc.connect_async(MQTT_ENDPOINT, port=MQTT_PORT, keepalive=60, bind_address="")
        self._mqttc.loop_start()

    def disconnect(self):
        self._mqttc.disconnect()