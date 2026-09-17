from __future__ import annotations
import logging
import random
import time
import warnings
from typing import Optional, Union

from . import aws_connection, connection, mqtt_connection
from .aws_connection import JciHitachiAuthError, JciHitachiDeviceError  # noqa: F401 (re-exported)
from .model import (
    JciHitachiAC,
    JciHitachiACSupport,
    JciHitachiAWSStatus,
    JciHitachiAWSStatusSupport,
    JciHitachiDH,
    JciHitachiDHSupport,
    JciHitachiStatus,
    JciHitachiStatusSupport,
)
from .status import (
    JciHitachiCommand,
    JciHitachiCommandAC,
    JciHitachiCommandDH,
    JciHitachiStatusInterpreter,
)

_LOGGER = logging.getLogger(__name__)


class Peripheral:  # pragma: no cover
    """Peripheral (Device) Information.

    Parameters
    ----------
    peripheral_json : dict
        Peripheral json of specific device.
    """

    supported_device_type = {
        144: "AC",
        146: "DH",
        # 148: "HE",
    }

    def __init__(self, peripheral_json: dict) -> None:
        self._json = peripheral_json
        self._available = False
        self._status_code = ""
        self._support_code = ""
        self._supported_status = None

        warnings.warn("This API has been deprecated.", DeprecationWarning)

    def __repr__(self) -> str:
        ret = (
            f"name: {self.name}\n"
            f"brand: {self.brand}\n"
            f"model: {self.model}\n"
            f"type: {self.type}\n"
            f"available: {self.available}\n"
            f"status_code: {self.status_code}\n"
            f"support_code: {self.support_code}\n"
            f"gateway_id: {self.gateway_id}\n"
            f"gateway_mac_address: {self.gateway_mac_address}"
        )
        return ret

    @classmethod
    def from_device_names(
        cls, peripherals_json: dict, device_names: Optional[Union[list[str], str]]
    ) -> dict[str, object]:
        """Use device names to pick peripheral_jsons accordingly.

        Parameters
        ----------
        peripherals_json : dict
            Peripherals_json retrieved from GetPeripheralsByUser.
        device_names : list of str or str or None
            Device name. If None is given, all available devices will be included, by default None.

        Returns
        -------
        dict
            A dict of Peripheral instances with device name key.
        """

        peripherals = {}

        if isinstance(device_names, str):
            device_names = [device_names]

        for result in peripherals_json["results"]:
            device_name = result["DeviceName"]
            device_type = result["Peripherals"][0]["DeviceType"]

            if device_names is None or (device_names and device_name in device_names):
                if device_type in cls.supported_device_type:
                    peripherals[device_name] = cls(result)

        assert device_names is None or len(device_names) == len(peripherals), (
            "Some of device_names are not available from the API."
        )

        return peripherals

    @property
    def available(self) -> bool:
        """Whether the device is available.

        Returns
        -------
        bool
            Return True if the device is available.
        """

        return self._available

    @available.setter
    def available(self, x) -> None:
        self._available = x

    @property
    def brand(self) -> str:
        """Device brand.

        Returns
        -------
        str
            Device brand.
        """

        return getattr(self.supported_status, "brand")

    @property
    def commander(self) -> Union[JciHitachiCommand, None]:
        """Return a new JciHitachiCommand instance based on peripheral's type.

        Returns
        -------
        JciHitachiCommand or None
            JciHitachiCommand instance.
        """

        if self.type == "AC":
            return JciHitachiCommandAC(self.gateway_mac_address)
        elif self.type == "DH":
            return JciHitachiCommandDH(self.gateway_mac_address)
        else:
            return None

    @property
    def gateway_id(self) -> int:
        """Gateway ID.

        Returns
        -------
        int
            Gateway ID.
        """

        return self._json["ObjectID"]

    @property
    def gateway_mac_address(self) -> str:
        """Gateway mac address.

        Returns
        -------
        str
            Gateway mac address.
        """

        return self._json["GMACAddress"]

    @property
    def model(self) -> str:
        """Device model.

        Returns
        -------
        str
            Device model.
        """

        return getattr(self.supported_status, "model")

    @property
    def name(self) -> str:
        """Device name.

        Returns
        -------
        str
            Device name.
        """

        return self._json["DeviceName"]

    @property
    def picked_peripheral(self) -> dict:
        """Picked peripheral.

        Returns
        -------
        dict
            Picked peripheral.
        """

        return self._json

    @property
    def status_code(self) -> str:
        """Peripheral's status code (LValue) reported by the API.

        Returns
        -------
        str
            Status code.
        """

        return self._status_code

    @status_code.setter
    def status_code(self, x: str) -> None:
        self._status_code = x

    @property
    def support_code(self) -> str:
        """Peripheral's support code (LValue) reported by the API.

        Returns
        -------
        str
            Status code.
        """

        return self._support_code

    @support_code.setter
    def support_code(self, x: str) -> None:
        self._support_code = x
        if self.type == "AC":
            self._supported_status = JciHitachiACSupport(
                JciHitachiStatusInterpreter(x).decode_support()
            )
        elif self.type == "DH":
            self._supported_status = JciHitachiDHSupport(
                JciHitachiStatusInterpreter(x).decode_support()
            )

    @property
    def supported_status(self) -> JciHitachiStatusSupport:
        """Peripheral's supported status converted from support_code.

        Returns
        -------
        JciHitachiStatusSupport
            Supported status.
        """

        return self._supported_status

    @property
    def type(self) -> str:
        """Device type.

        Returns
        -------
        str
            Device type.
            If not supported, 'unknown' will be returned. (currently supports: `AC`, `DH`)
        """

        return self.supported_device_type.get(
            self._json["Peripherals"][0]["DeviceType"], "unknown"
        )


class JciHitachiAPI:  # pragma: no cover
    """Jci-Hitachi API.

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    device_names : list of str or str or None, optional
        Device names. If None is given, all available devices will be included, by default None.
    max_retries : int, optional
        Maximum number of retries when setting status, by default 5.
    device_offline_timeout: float, optional
        Device offline timeout, by default 45.0.
    print_response : bool, optional
        If set, all responses of httpx and MQTT will be printed, by default False.
    """

    def __init__(
        self,
        email: str,
        password: str,
        device_names: Optional[Union[list[str], str]] = None,
        max_retries: int = 5,
        device_offline_timeout: float = 45.0,
        print_response: bool = False,
    ) -> None:
        self.email = email
        self.password = password
        self.device_names = device_names
        self.max_retries = max_retries
        self.device_offline_timeout = device_offline_timeout
        self.print_response = print_response

        self._mqtt = None
        self._device_id = random.randint(1000, 6999)
        self._peripherals = {}
        self._session_token = None
        self._user_id = None
        self._task_id = 0

        warnings.warn("This API has been deprecated.", DeprecationWarning)

    @property
    def peripherals(self) -> dict[str, Peripheral]:
        """Picked peripherals.

        Returns
        -------
        dict
            A dict of Peripherals.
        """

        return self._peripherals

    @property
    def user_id(self) -> Optional[int]:
        """User ID.

        Returns
        -------
        int
            User ID.
        """

        return self._user_id

    @property
    def task_id(self) -> int:
        """Task ID.

        Returns
        -------
        int
            Serial number counted from 0, with maximum 999.
        """

        self._task_id += 1
        if self._task_id >= 1000:
            self._task_id = 1

        return self._task_id

    def _sync_peripherals_availablity(self) -> None:
        device_access_time = self._mqtt.mqtt_events.device_access_time
        for peripheral in self._peripherals.values():
            if (
                peripheral.gateway_id in device_access_time
                and abs(time.time() - device_access_time[peripheral.gateway_id])
                < self.device_offline_timeout
            ):
                peripheral.available = True
            else:
                peripheral.available = False

    def login(self) -> None:
        """Login API.

        Raises
        ------
        RuntimeError
            If a login error occurs, RuntimeError will be raised.
        """

        conn = connection.GetPeripheralsByUser(
            self.email, self.password, print_response=self.print_response
        )
        conn_status, conn_json = conn.get_data()
        self._session_token = conn.session_token

        if conn_status == "OK":
            if len(conn_json["results"]) != 0:
                self._user_id = conn_json["results"][0]["Owner"]

            # peripherals
            self._peripherals = Peripheral.from_device_names(
                conn_json, self.device_names
            )
            self.device_names = list(self._peripherals.keys())

            # mqtt
            self._mqtt = mqtt_connection.JciHitachiMqttConnection(
                self.email,
                self.password,
                self._user_id,
                print_response=self.print_response,
            )
            self._mqtt.configure()
            self._mqtt.connect()

            # status
            self.refresh_status()

        else:
            raise RuntimeError(f"An error occurred when API login: {conn_status}.")

    def logout(self) -> None:
        """Logout API."""

        self._mqtt.disconnect()

    def change_password(self, new_password: str) -> None:
        """Change password.

        Parameters
        ----------
        new_password : str
            New password.

        Raises
        ------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        conn = connection.UpdateUserCredential(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response,
        )
        conn_status, conn_json = conn.get_data(new_password)
        self._session_token = conn.session_token

    def get_status(
        self, device_name: Optional[str] = None
    ) -> dict[str, JciHitachiStatus]:
        """Get device status after refreshing status.

        Parameters
        ----------
        device_name : str, optional
            Getting a device's status by its name.
            If None is given, all devices' status will be returned,
            by default None.

        Returns
        -------
        dict of JciHitachiStatus.
            Return a dict of JciHitachiStatus instances according to device type.
            For example, if the device type is `AC`, then return JciHitachiAC instance.
        """

        statuses = {}
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or peripheral.type == "unknown":
                continue
            dev_status = JciHitachiStatusInterpreter(
                peripheral.status_code
            ).decode_status()

            if peripheral.type == "AC":
                statuses[name] = JciHitachiAC(dev_status)
            elif peripheral.type == "DH":
                statuses[name] = JciHitachiDH(dev_status)
        return statuses

    def get_supported_status(
        self, device_name: Optional[str] = None
    ) -> dict[str, JciHitachiStatusSupport]:
        """Get supported device status after refreshing status.

        Parameters
        ----------
        device_name : str, optional
            Getting a device's status by its name.
            If None is given, all devices' status will be returned,
            by default None.

        Returns
        -------
        dict of JciHitachiStatusSupport.
            Return a dict of JciHitachiStatusSupport instances according to device type.
            For example, if the device type is `AC`, then return JciHitachiACSupport instance.
        """

        supported_statuses = {}
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or peripheral.type == "unknown":
                continue
            supported_statuses[name] = peripheral.supported_status

        return supported_statuses

    def refresh_status(self, device_name: Optional[str] = None) -> None:
        """Refresh device status from the API.

        Parameters
        ----------
        device_name : str, optional
            Refreshing a device's status by its name.
            If None is given, all devices' status will be refreshed,
            by default None.

        Raises
        ------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        self._sync_peripherals_availablity()

        conn = connection.GetDataContainerByID(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response,
        )
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or peripheral.type == "unknown":
                continue
            conn_status, conn_json = conn.get_data(peripheral.picked_peripheral)
            self._session_token = conn.session_token

            if conn_status == "OK":
                peripheral.support_code = conn_json["results"]["DataContainer"][0][
                    "ContDetails"
                ][0]["LValue"]
                peripheral.status_code = conn_json["results"]["DataContainer"][0][
                    "ContDetails"
                ][1]["LValue"]
            else:
                raise RuntimeError(
                    f"An error occurred when refreshing status: {conn_status}"
                )

    def set_status(self, status_name: str, status_value: int, device_name: str) -> bool:
        """Set status to a peripheral.

        Parameters
        ----------
        status_name : str
            Status name, which has to be in idx dict. E.g. JciHitachiAC.idx
        status_value : int
            Status value.
        device_name : str
            Device name.

        Returns
        -------
        bool
            Return True if the command has been successfully executed. Otherwise, return False.

        Raises
        ------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        self._sync_peripherals_availablity()
        if not self._peripherals[device_name].available:
            return False

        commander = self._peripherals[device_name].commander

        conn = connection.CreateJob(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response,
        )
        conn2 = connection.GetJobDoneReport(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response,
        )

        # The mqtt events occurring order:
        # job (occurs one time) ->
        # job_done_report (occurs many times until the job status is successful) ->
        # peripheral (occurs one time, if this step is timed out, the job command fails)
        self._mqtt.mqtt_events.job.clear()
        self._mqtt.mqtt_events.job_done_report.clear()
        self._mqtt.mqtt_events.peripheral.clear()

        conn_status, conn_json = conn.get_data(
            gateway_id=self._peripherals[device_name].gateway_id,
            device_id=self._device_id,
            task_id=self.task_id,
            job_info=commander.get_b64command(status_name, status_value),
        )
        self._session_token = conn.session_token

        if not self._mqtt.mqtt_events.job.wait(timeout=10.0):
            return False
        for _ in range(self.max_retries):
            if not self._mqtt.mqtt_events.job_done_report.wait(timeout=10.0):
                self._mqtt.mqtt_events.job_done_report.clear()
                continue
            conn_status, conn_json = conn2.get_data(device_id=self._device_id)
            if (
                conn_status == "OK"
                and len(conn_json["results"]) != 0
                and conn_json["results"][0]["JobStatus"] == 0
            ):
                if not self._mqtt.mqtt_events.peripheral.wait(timeout=10.0):
                    return False
                time.sleep(0.5)  # still needs to wait a moment.
                return True
        return False


class AWSThing:
    """AWS thing (device) information.

    Parameters
    ----------
    thing_json : dict
        Thing json of a specific device.
    """

    supported_device_type = {
        "1": "AC",
        "2": "DH",
        "3": "HE",
        # "4": "PM25_PANEL",
    }

    def __init__(self, thing_json: dict) -> None:
        self._json: dict = thing_json
        self._available: bool = True
        self._attention_reason: Optional[str] = None
        self._attention: Optional[dict] = None
        self._shadow: Optional[dict] = None
        self._status_code: Optional[JciHitachiAWSStatus] = None
        self._support_code: Optional[JciHitachiAWSStatusSupport] = None
        self._monthly_data: Optional[list[dict]] = None

    def __repr__(self) -> str:
        ret = (
            f"name: {self.name}\n"
            f"brand: {self.brand}\n"
            f"model: {self.model}\n"
            f"type: {self.type}\n"
            f"firmware_code: {self.firmware_code}\n"
            f"firmawre_version: {self.firmware_version}\n"
            f"available: {self.available}\n"
            f"status_code: {self.status_code}\n"
            f"support_code: {self.support_code}\n"
            f"shadow: {self.shadow}\n"
            f"gateway_mac_address: {self.gateway_mac_address}"
        )
        return ret

    @classmethod
    def from_device_names(
        cls, things_json: dict, device_names: Optional[Union[list[str], str]]
    ) -> dict[str, object]:
        """Use device names to pick things_json accordingly.

        Parameters
        ----------
        things_json : dict
            things_json retrieved from aws_connection.GetAllDevice.
        device_names : list of str or str or None
            Device name. If None is given, all available devices will be included, by default None.

        Returns
        -------
        dict
            A dict of AWSThing instances with device name key.
        """

        things = {}

        if isinstance(device_names, str):
            device_names = [device_names]

        for thing in things_json["results"]["Things"]:
            device_name = thing["CustomDeviceName"]
            device_type = thing["DeviceType"]

            if device_names is None or (device_names and device_name in device_names):
                if device_type in cls.supported_device_type:
                    things[device_name] = cls(thing)

        assert device_names is None or len(device_names) == len(things), (
            "Some of device_names are not available from the API."
        )

        return things

    @property
    def available(self) -> bool:
        """Whether the device is available.

        Returns
        -------
        bool
            Return True if the device is available.
        """

        return self._available

    @available.setter
    def available(self, x: bool) -> None:
        self._available = x

    @property
    def attention_reason(self) -> Optional[str]:
        """Why the device is unavailable, or None when the last refresh succeeded.

        Set by `JciHitachiAWSAPI.refresh_status()` when this device (and only this device)
        timed out or answered with a payload the library cannot decode.

        Returns
        -------
        str or None
            Human-readable reason.
        """

        return self._attention_reason

    @attention_reason.setter
    def attention_reason(self, x: Optional[str]) -> None:
        self._attention_reason = x

    @property
    def attention(self) -> Optional[dict]:
        """Structured form of `attention_reason`, or None when the last refresh succeeded.

        Keys:

        - ``request``: ``"support code"``, ``"status code"`` or ``"shadow"``
        - ``topic``: the answer topic (``"registration/response"``, ``"status/response"``) or
          ``"shadow/name/info/get"``
        - ``cause``: ``"undecodable"`` (an answer arrived that is not JSON), ``"no_data"`` (no
          JSON answer arrived in this refresh) or ``"timeout"`` (sending the request failed)
        - ``payload_length`` / ``payload_hex``: size of the undecodable answer and the hex of at
          most its first 64 bytes; None for the other causes

        ``no_data`` is what a timeout of the answer looks like with this library: the waiter in
        `JciHitachiAWSMqttConnection.publish()` does not check the result of ``Event.wait()``,
        so a request that got no answer still counts as executed.

        Returns
        -------
        dict or None
            See above.
        """

        return self._attention

    @attention.setter
    def attention(self, x: Optional[dict]) -> None:
        self._attention = x

    # Last control round trip, kept for diagnostics (set by JciHitachiAWSAPI.set_status()):
    # the request that was sent, when, and the raw answer (dict if JSON, bytes if not,
    # None if the device did not answer).
    last_control_at: Optional[float] = None
    last_control_request: Optional[dict] = None
    last_control_response: Optional[Union[dict, bytes]] = None

    @property
    def brand(self) -> Optional[str]:
        """Device brand.

        Returns
        -------
        str or None
            Device brand; None until the support code has been read.
        """

        return getattr(self._support_code, "Brand", None)

    @property
    def firmware_version(self) -> str:
        """Firmware version.

        Returns
        -------
        str
            Device firmware version.
        """

        return getattr(self._support_code, "FirmwareVersion", None)

    @property
    def firmware_code(self) -> str:
        """Firmware code.

        Returns
        -------
        str
            Device firmware code.
        """

        return getattr(self._support_code, "FirmwareCode", None)

    @property
    def gateway_mac_address(self) -> str:
        """Gateway mac address.

        Returns
        -------
        str
            Gateway mac address.
        """

        return self._json["ThingName"].split("_")[-1]

    @property
    def model(self) -> str:
        """Device model.

        Returns
        -------
        str
            Device model.
        """

        model = getattr(self._support_code, "Model", None)
        # Observed 2026-09-16 (RAD-series AC, FirmwareVersion 6.0.032): the cloud's
        # registration/response carried "Model": "RAD-\xffR", i.e. the value is
        # corrupted at the source. Return None rather than a string with control characters;
        # the real model cannot be recovered from the payload.
        if isinstance(model, str) and not model.isprintable():
            return None
        return model

    @property
    def name(self) -> str:
        """Device name.

        Returns
        -------
        str
            Device name.
        """

        return self._json["CustomDeviceName"]

    @property
    def picked_thing(self) -> dict:
        """Picked thing.

        Returns
        -------
        dict
            Picked thing.
        """

        return self._json

    @property
    def shadow(self) -> Optional[dict]:
        """Thing's shadow reported by the API.

        Returns
        -------
        dict
            Shadow.
        """

        return self._shadow

    @shadow.setter
    def shadow(self, x: dict) -> None:
        self._shadow = x

    @property
    def status_code(self) -> Optional[JciHitachiAWSStatus]:
        """Thing's status code reported by the API.

        Returns
        -------
        JciHitachiAWSStatus
            Status code.
        """

        return self._status_code

    @status_code.setter
    def status_code(self, x: JciHitachiAWSStatus) -> None:
        self._status_code = x

    @property
    def support_code(self) -> Optional[JciHitachiAWSStatusSupport]:
        """Thing's support code reported by the API.

        Returns
        -------
        JciHitachiAWSStatusSupport
            Status code.
        """

        return self._support_code

    @support_code.setter
    def support_code(self, x: JciHitachiAWSStatusSupport) -> None:
        self._support_code = x

    @property
    def monthly_data(self) -> Optional[list[dict]]:
        """Thing's monthly data reported by the API.

        Returns
        -------
        Optional[list[dict]]
            Monthly data.
        """

        return self._monthly_data

    @monthly_data.setter
    def monthly_data(self, x: Optional[list[dict]]) -> None:
        self._monthly_data = x

    @property
    def thing_name(self) -> str:
        return self._json["ThingName"]

    @property
    def type(self) -> str:
        """Device type.

        Returns
        -------
        str
            Device type.
            If not supported, 'unknown' will be returned.
        """

        return self.supported_device_type.get(self._json["DeviceType"], "unknown")


class JciHitachiAWSAPI:
    """Jci-Hitachi API.

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    device_names : list of str or str or None, optional
        Device names. If None is given, all available devices will be included, by default None.
    max_retries : int, optional
        Maximum number of retries when setting status, by default 5.
    device_offline_timeout: float, optional
        For future use.
    print_response : bool, optional
        If set, all responses of httpx and MQTT will be printed, by default False.
    """

    def __init__(
        self,
        email: str,
        password: str,
        device_names: Optional[Union[list[str], str]] = None,
        max_retries: int = 5,
        device_offline_timeout: float = 10.0,
        print_response: bool = False,
    ) -> None:
        self.email: str = email
        self.password: str = password
        self.device_names: Optional[Union[list[str], str]] = device_names
        self.max_retries: int = max_retries
        self.print_response: bool = print_response

        self._mqtt: Optional[aws_connection.JciHitachiAWSMqttConnection] = None
        self._mqtt_timeout: float = device_offline_timeout
        self._shadow_names: Union[str, list] = ["info"]
        self._device_id: int = random.randint(1000, 6999)
        self._things: dict[str, AWSThing] = {}
        self._aws_tokens: Optional[aws_connection.AWSTokens] = None
        self._aws_identity: Optional[aws_connection.AWSIdentity] = None
        self._task_id: int = 0

    @property
    def things(self) -> dict[str, AWSThing]:
        """Picked things.

        Returns
        -------
        dict of AWSThing
            A dict of AWSThing instances.
        """

        return self._things

    @property
    def task_id(self) -> int:
        """Task ID.

        Returns
        -------
        int
            Serial number counted from 0, with maximum 999.
        """

        self._task_id += 1
        if self._task_id >= 1000:
            self._task_id = 1

        return self._task_id

    def _check_before_publish(self) -> None:
        # Reauthenticate 5 mins before AWSTokens expiration.
        current_time = time.time()
        if self._aws_tokens is None or (
            self._aws_tokens.expiration - current_time <= 300
        ):
            self.reauth()

        if self._mqtt.mqtt_events.mqtt_error_event.is_set():
            self._mqtt.mqtt_events.mqtt_error_event.clear()
            self.reauth()

    def _get_valid_things(
        self, device_name: Optional[str] = None
    ) -> tuple[str, AWSThing]:
        for name, thing in self._things.items():
            if (device_name and name != device_name) or thing.type == "unknown":
                continue
            yield name, thing

    def _delay(self) -> None:
        time.sleep(0.2)

    def login(self) -> None:
        """Login API.

        Login succeeds once the account is authenticated, the device list is retrieved and the
        MQTT connection is up. Devices are then refreshed individually: a device that times out
        or answers with an undecodable payload is marked `available = False` with an
        `attention_reason`, and the other devices stay usable. Even when every device fails,
        login returns normally (with a warning) so callers can keep polling until they recover.

        Raises
        ------
        JciHitachiAuthError
            If AWS Cognito rejects the credentials (subclass of RuntimeError).
        RuntimeError
            If the device list cannot be retrieved or the MQTT connection fails.
        """

        conn = aws_connection.GetUser(
            email=self.email,
            password=self.password,
            print_response=self.print_response,
        )
        self._aws_tokens = conn.aws_tokens
        conn_status, self._aws_identity = conn.get_data()
        if conn_status != "OK":
            raise aws_connection.cognito_error(
                conn_status, "An error occurred when retrieving the user identity"
            )

        conn = aws_connection.GetAllDevice(
            self._aws_tokens, print_response=self.print_response
        )
        conn_status, conn_json = conn.get_data()

        if conn_status == "OK":
            # things
            self._things = AWSThing.from_device_names(conn_json, self.device_names)
            self.device_names = list(self._things.keys())
            thing_names = [value.thing_name for value in self._things.values()]

            # mqtt
            def get_credential_callable():
                self._check_before_publish()
                conn = aws_connection.GetCredentials(
                    email=self.email,
                    password=self.password,
                    aws_tokens=self._aws_tokens,
                    print_response=self.print_response,
                )
                conn_status, aws_credentials = conn.get_data(self._aws_identity)
                if conn_status != "OK":
                    aws_connection._LOGGER.error(
                        f"An error occurred when acquiring a new AwsCredentials: {conn_status}"
                    )
                return aws_credentials

            self._mqtt = aws_connection.JciHitachiAWSMqttConnection(
                get_credential_callable, print_response=self.print_response
            )
            self._mqtt.configure(self._aws_identity.identity_id)

            if not self._mqtt.connect(
                self._aws_identity.host_identity_id, self._shadow_names, thing_names
            ):
                raise RuntimeError(
                    "An error occurred when connecting to MQTT endpoint."
                )

            # status
            try:
                self.refresh_status(refresh_support_code=True, refresh_shadow=True)
            except JciHitachiDeviceError as e:
                # Every device failed, but the account and the MQTT session are fine: keep the
                # connection so the caller can keep polling; each thing carries its own reason.
                _LOGGER.warning(f"Logged in, but no device is available yet: {e}")
            except Exception:
                # Do not leak a live MQTT session (and its subscriptions) behind a failed login.
                self._mqtt.disconnect()
                raise
        else:
            raise RuntimeError(
                f"An error occurred when retrieving devices info: {conn_status}"
            )

    def logout(self) -> None:
        """Logout API."""

        self._mqtt.disconnect()

    def reauth(self) -> None:
        """Reauthenticate with AWS Cognito Service."""

        conn = aws_connection.JciHitachiAWSCognitoConnection(
            email=self.email,
            password=self.password,
            aws_tokens=self._aws_tokens,
            print_response=self.print_response,
        )
        conn_status, self._aws_tokens = conn.login(use_refresh_token=False)
        if conn_status != "OK":
            raise RuntimeError(
                f"An error occurred when reauthenticating with AWS Cognito Service: {conn_status}"
            )

    def change_password(self, new_password: str) -> None:
        """Change password.

            Warning:
            Use this function carefully, be sure you specify a strong enough password;
            otherwise, your password might be accepted by the Hitachi account management but not be accepted by AWS Cognito or vice versa,
            which will result in a login failure in the APP.

        Parameters
        ----------
        new_password : str
            New password.

        Raises
        ------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        # We have to change the password in both AWS Cognito and Hitachi owned account management simultaneously.
        conn = aws_connection.ChangePassword(
            self.email,
            self.password,
            aws_tokens=self._aws_tokens,
            print_response=self.print_response,
        )
        aws_conn_status, _ = conn.get_data(new_password)
        if aws_conn_status != "OK":
            raise RuntimeError(
                f"An error occurred when changing AWS Cognito password: {aws_conn_status}"
            )

        conn = connection.UpdateUserCredential(
            self.email, self.password, print_response=self.print_response
        )
        hitachi_conn_status, _ = conn.get_data(new_password)
        if hitachi_conn_status != "OK":
            raise RuntimeError(
                f"An error occurred when changing Hitachi password: {hitachi_conn_status}"
            )

    def refresh_monthly_data(self, months: int, device_name: str) -> None:
        """Refresh available monthly data (power consumption) from the API.

        Parameters
        ----------
        months : int
            Number of months to get.
        device_name : str
            Device name.

        Raises
        ------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        thing = self._things[device_name]
        current_timestamp_millis = time.time() * 1000

        conn = aws_connection.GetAvailableAggregationMonthlyData(
            self._aws_tokens, print_response=self.print_response
        )

        conn_status, response = conn.get_data(
            thing.thing_name,
            int(
                current_timestamp_millis - months * 2678400000
            ),  # 2678400000 ms == 31 days
            int(current_timestamp_millis),
        )
        if conn_status != "OK":
            raise RuntimeError(
                f"An error occurred when getting monthly data: {conn_status}"
            )

        thing.monthly_data = sorted(
            response["results"]["Data"], key=lambda x: x["Timestamp"]
        )

    def refresh_status(
        self,
        device_name: Optional[str] = None,
        refresh_support_code: bool = False,
        refresh_shadow: bool = False,
    ) -> None:
        """Refresh device status from the API.

        Parameters
        ----------
        device_name : str, optional
            Refreshing a device's status by its name.
            If None is given, all devices' status will be refreshed,
            by default None.
        refresh_support_code : bool, optional
            Whether or not to refresh support code, by default False.
        refresh_shadow : bool, optional
            Whether or not to refresh AWS IoT Shadow, by default False.

        A device whose status request times out or is answered with an undecodable payload
        is marked `available = False`; the other devices are refreshed normally. A failed
        support code or shadow request only sets `attention_reason` and keeps the device
        available if its status arrived. Only when the status request failed for every
        requested device is an exception raised.

        Raises
        ------
        JciHitachiDeviceError
            If the status request failed for every requested device (subclass of
            RuntimeError). The message lists each device's reason.
        """

        # queue tasks
        for name, thing in self._get_valid_things(device_name):
            self._check_before_publish()

            if refresh_support_code:
                self._mqtt.publish(
                    self._aws_identity.host_identity_id,
                    thing.thing_name,
                    "support",
                    self._mqtt_timeout,
                )
            if refresh_shadow:
                self._mqtt.publish_shadow(thing.thing_name, "get", shadow_name="info")

            self._mqtt.publish(
                self._aws_identity.host_identity_id,
                thing.thing_name,
                "status",
                self._mqtt_timeout,
            )

        # execute
        support_results, shadow_results, status_results, _ = self._mqtt.execute()

        # gather results, one device at a time; a failure only affects that device
        reasons: list[str] = []
        requested = 0
        for name, thing in self._get_valid_things(device_name):
            requested += 1
            # every channel is stored if it arrived (the shadow often works while the
            # status/support channel does not); the first failure becomes the reason.
            # Only the status channel decides availability: on 2026-09-17 13:07 all three
            # units of an account answered registration/response with a non-JSON frame on
            # every poll while status/response was JSON, and treating that as a device
            # failure discarded the status of every device.
            failures: list[Optional[tuple[str, dict]]] = []
            if refresh_support_code:
                failures.append(
                    self._gather_one(
                        name,
                        thing,
                        "support code",
                        "registration",
                        support_results,
                        self._mqtt.mqtt_events.device_support,
                        lambda v: setattr(thing, "support_code", v),
                    )
                )
            if refresh_shadow:
                failures.append(
                    self._gather_one(
                        name,
                        thing,
                        "shadow",
                        None,
                        shadow_results,
                        self._mqtt.mqtt_events.device_shadow,
                        lambda v: setattr(thing, "shadow", v),
                    )
                )
            status_failure = self._gather_one(
                name,
                thing,
                "status code",
                "status",
                status_results,
                self._mqtt.mqtt_events.device_status,
                lambda v: setattr(thing, "status_code", v),
            )
            failures.append(status_failure)
            failed = [f for f in failures if f is not None]
            if status_failure is not None:
                # unavailable because of the status: every failed channel in request order
                # (so the status failure is never hidden behind an earlier one), and the
                # structured attention describes the status failure
                reason = " ".join(f[0] for f in failed)
                first = status_failure
            else:
                first = failed[0] if failed else None
                reason = first[0] if first is not None else None

            previous_reason = thing.attention_reason
            was_available = thing.available
            thing.available = status_failure is None
            thing.attention_reason = reason
            thing.attention = first[1] if first is not None else None
            if thing.available and not was_available and previous_reason is not None:
                _LOGGER.info(f"{name} is available again.")
            if status_failure is not None:
                reasons.append(reason)
            # log on change only; a permanently failing device would otherwise
            # produce one line per poll
            if reason is not None and reason != previous_reason:
                if thing.available:
                    _LOGGER.warning(f"{name} needs attention: {reason}")
                else:
                    _LOGGER.warning(f"{name} is unavailable: {reason}")

        if requested and len(reasons) == requested:
            raise JciHitachiDeviceError(" | ".join(reasons))

    def _gather_one(
        self,
        name: str,
        thing: AWSThing,
        what: str,
        kind: Optional[str],
        results: Optional[list],
        data: dict,
        store,
    ) -> Optional[tuple[str, dict]]:
        """Store one device's `what` result; return (reason, attention) on failure, None on success.

        `kind` is the MQTT topic kind (`registration`, `status`) used to look up an undecodable
        answer recorded by the connection; None for the shadow, which has no such record.
        """

        if results is not None and thing.thing_name in results:
            if thing.thing_name in data:
                store(data[thing.thing_name])
                return None
            undecodable = (
                self._mqtt.mqtt_events.device_undecodable.get(thing.thing_name, {}).get(
                    kind
                )
                if kind is not None
                else None
            )
            if undecodable is not None:
                topic, payload = undecodable
                # Only what was observed: the topic answered and the bytes. What the frame
                # means is unknown (seen as fc ff ff 1f 01 01 from RAD-series ACs, 2026-08/09).
                return (
                    f"{name} answered the {what} request on {kind}/response with a "
                    f"payload that is not JSON (hex {payload.hex()}); its meaning is unknown.",
                    self._attention(what, kind, "undecodable", payload),
                )
            return (
                f"An event occurred but wasn't accompanied with data when refreshing {name} {what}.",
                self._attention(what, kind, "no_data"),
            )
        return (
            f"Timed out refreshing {name} {what}. Please ensure the device is online and avoid opening the official app.",
            self._attention(what, kind, "timeout"),
        )

    @staticmethod
    def _attention(
        what: str, kind: Optional[str], cause: str, payload: Optional[bytes] = None
    ) -> dict:
        """Structured reason for `AWSThing.attention` (see there for the keys)."""

        return {
            "request": what,
            "topic": f"{kind}/response" if kind is not None else "shadow/name/info/get",
            "cause": cause,
            "payload_length": len(payload) if payload is not None else None,
            "payload_hex": payload[:64].hex() if payload is not None else None,
        }

    def get_status(
        self, device_name: Optional[str] = None, legacy: bool = False
    ) -> dict[str, JciHitachiAWSStatus]:
        """Get device status after refreshing status.

        Parameters
        ----------
        device_name : str, optional
            Getting a device's status by its name.
            If None is given, all devices' status will be returned,
            by default None.
        legacy : bool, optional
            Whether or not to return status with legacy status name, by default False.

        Returns
        -------
        dict of JciHitachiAWSStatus.
            A dict of JciHitachiAWSStatus instances.
        """

        statuses = {}
        for name, thing in self._get_valid_things(device_name):
            if thing.status_code is None:
                # never refreshed successfully (see thing.attention_reason); nothing to report
                continue
            if legacy:
                statuses[name] = thing.status_code.legacy_status
            else:
                statuses[name] = thing.status_code

            # inject temp and humidity limitations from the support code, if it was read
            if thing.support_code is None:
                continue
            if thing.type == "AC":
                statuses[name]._status["max_temp"] = thing.support_code.max_temp
                statuses[name]._status["min_temp"] = thing.support_code.min_temp
            elif thing.type == "DH":
                statuses[name]._status["max_humidity"] = thing.support_code.max_humidity
                statuses[name]._status["min_humidity"] = thing.support_code.min_humidity

        return statuses

    def set_status(
        self,
        status_name: str,
        device_name: str,
        status_value: int = None,
        status_str_value: str = None,
    ) -> bool:
        """Set status to a thing. Either status_value or status_str_value must be specified.

        Parameters
        ----------
        status_name : str
            Status name.
        device_name : str
            Device name.
        status_value : int, optional
            Status value, by default None.
        status_str_value : str, optional
            Status string value, by default None.

        Returns
        -------
        bool
            Return True if the command has been successfully executed. Otherwise, return False.

        Raises
        ------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        self._check_before_publish()

        thing = self._things[device_name]

        is_valid, status_name, status_value = JciHitachiAWSStatus.str2id(
            device_type=thing.type,
            status_name=status_name,
            status_value=status_value,
            status_str_value=status_str_value,
            support_code=thing.support_code,
        )

        if not is_valid:
            return False

        shadow_publish_mapping = {
            "CleanFilterNotification": "filter",
            "CleanNotification": "filter",
            "CleanSecondaryFilterNotification": "filter",
            "FrontFilterNotification": "filter",
            "Pm25FilterNotification": "filter",
            "enableQAMode": "qa",
        }

        if False:  # status_name in shadow_publish_mapping: # TODO: replace False cond after shadow function is completed.
            shadow_publish_schema = {}
            if (
                shadow_publish_mapping[status_name] == "filter"
                or shadow_publish_mapping[status_name] == "qa"
            ):
                shadow_publish_schema.update({status_name: bool(status_value)})
                # if thing.type == "AC": # there is an additional parameter for AC
                #    shadow_publish_schema.update("FilterElapsedHour", 0 if status_value == 0 else status_value)
            self._mqtt.publish_shadow(
                thing.thing_name,
                "update",
                {"state": {"reported": {**shadow_publish_schema}}},
                shadow_name="info",
            )
            if self._mqtt.mqtt_events.device_control_event.wait(
                timeout=self._mqtt_timeout
            ):
                device_control = self._mqtt.mqtt_events.device_control.get(
                    thing.thing_name
                )
                if device_control["state"]["reported"][status_name] == bool(
                    status_value
                ):
                    self._mqtt.mqtt_events.device_control_event.clear()
                    self._delay()
                    return True
            return False

        request = {
            status_name: status_value,
            "TaskID": self.task_id,
            "Timestamp": int(time.time()),
        }
        # forget an earlier non-JSON control answer so it cannot be taken for this one
        self._mqtt.mqtt_events.device_undecodable.get(thing.thing_name, {}).pop(
            "control", None
        )
        thing.last_control_at = time.time()
        thing.last_control_request = dict(request)
        thing.last_control_response = None

        self._mqtt.publish(
            self._aws_identity.host_identity_id,
            thing.thing_name,
            "control",
            self._mqtt_timeout,
            request,
        )

        _, _, _, control_results = self._mqtt.execute(control=True)

        if thing.thing_name not in control_results:
            _LOGGER.warning(
                f"{device_name} did not answer the control request {status_name}={status_value} "
                f"within {self._mqtt_timeout} s."
            )
            return False

        device_control = self._mqtt.mqtt_events.device_control.get(thing.thing_name)
        if device_control is None:
            # the event fired without JSON data: the device answered the control request
            # with an undecodable payload (recorded in mqtt_events.device_undecodable)
            undecodable = self._mqtt.mqtt_events.device_undecodable.get(
                thing.thing_name, {}
            ).get("control")
            if undecodable:
                thing.last_control_response = undecodable[1]
            _LOGGER.warning(
                f"{device_name} did not acknowledge {status_name}: "
                + (
                    f"undecodable control response (hex {undecodable[1].hex()})"
                    if undecodable
                    else "control response carried no data"
                )
            )
            return False

        thing.last_control_response = dict(device_control)
        # The echo means the cloud accepted the request, not that the device carried it out:
        # on 2026-09-17 four CleanSwitch=1 commands were echoed with Error 0 while the units
        # stayed idle (contract/profiles/ac-rad-fw6.0.032, freeze_clean). The value cached below
        # is replaced by the device's own value on the next refresh_status.
        if device_control.get(status_name) == status_value:
            thing.status_code.set_new_status(status_name, status_value)
            return True
        _LOGGER.warning(
            f"{device_name} answered the control request {status_name}={status_value} "
            f"with {status_name}={device_control.get(status_name)!r}."
        )
        return False
