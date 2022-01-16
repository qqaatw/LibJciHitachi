import random
import time
import warnings
from typing import Dict, List, Optional, Union

from . import aws_connection, connection, mqtt_connection
from .status import (
    JciHitachiCommand,
    JciHitachiCommandAC,
    JciHitachiCommandDH,
    JciHitachiStatusInterpreter,
)
from .model import (
    JciHitachiStatusSupport,
    JciHitachiACSupport,
    JciHitachiDHSupport,
    JciHitachiStatus,
    JciHitachiAC,
    JciHitachiDH,
    JciHitachiAWSStatusSupport,
    JciHitachiAWSStatus,
)


class Peripheral:
    """Peripheral (Device) Information.

    Parameters
    ----------
    peripheral_json : dict
        Peripheral json of specific device.
    """

    supported_device_type = {
        144: "AC",
        146: "DH",
        #148: "HE",
    }

    def __init__(self, peripheral_json : dict) -> None:
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
        cls,
        peripherals_json : dict,
        device_names : Optional[Union[List[str], str]]
    ) -> Dict[str, object]:
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

        assert device_names is None or len(device_names) == len(peripherals), \
            "Some of device_names are not available from the API."

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

        return self._json['DeviceName']

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
    def status_code(self, x : str) -> None:
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
    def support_code(self, x : str) -> None:
        self._support_code = x
        if self.type == "AC" :
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
            self._json['Peripherals'][0]['DeviceType'],
            'unknown'
        )


class JciHitachiAPI:
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

    def __init__(self, 
        email : str,
        password : str,
        device_names : Optional[Union[List[str], str]] = None,
        max_retries : int = 5,
        device_offline_timeout : float = 45.0,
        print_response: bool = False
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
    def peripherals(self) -> Dict[str, Peripheral]:
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
            Serial number counted from 0.
        """

        self._task_id += 1
        return self._task_id

    def _sync_peripherals_availablity(self) -> None:
        device_access_time = self._mqtt.mqtt_events.device_access_time
        for peripheral in self._peripherals.values():
            if peripheral.gateway_id in device_access_time and \
                abs(time.time() - device_access_time[peripheral.gateway_id]) < self.device_offline_timeout:
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
            self.email,
            self.password,
            print_response=self.print_response)
        conn_status, conn_json = conn.get_data()
        self._session_token = conn.session_token

        if conn_status == "OK":
            if len(conn_json["results"]) != 0:
                self._user_id = conn_json["results"][0]["Owner"]

            # peripherals
            self._peripherals = Peripheral.from_device_names(
                conn_json,
                self.device_names
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
            raise RuntimeError(
                f"An error occurred when API login: {conn_status}.")
    
    def logout(self) -> None:
        """Logout API.
        """
        
        self._mqtt.disconnect()

    def change_password(self, new_password : str) -> None:
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
            print_response=self.print_response
        )
        conn_status, conn_json = conn.get_data(new_password)
        self._session_token = conn.session_token

    def get_status(self, device_name: Optional[str] = None) -> Dict[str, JciHitachiStatus]:
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
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            dev_status = JciHitachiStatusInterpreter(peripheral.status_code).decode_status()

            if peripheral.type == "AC":
                statuses[name] = JciHitachiAC(dev_status)
            elif peripheral.type == "DH":
                statuses[name] = JciHitachiDH(dev_status)
        return statuses
    
    def get_supported_status(self, device_name: Optional[str] = None) -> Dict[str, JciHitachiStatusSupport]:
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
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            supported_statuses[name] = peripheral.supported_status
        
        return supported_statuses

    def refresh_status(self, device_name : Optional[str] = None) -> None:
        """Refresh device status from the API.

        Parameters
        ----------
        device_name : str, optional
            Refreshing a device's status by its name.
            If None is given, all devices' status will be refreshed,
            by default None.
        
        Raise
        -------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        self._sync_peripherals_availablity()

        conn = connection.GetDataContainerByID(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response
        )
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            conn_status, conn_json = conn.get_data(
                peripheral.picked_peripheral
            )
            self._session_token = conn.session_token

            if conn_status == 'OK':
                peripheral.support_code = conn_json["results"]["DataContainer"][0]["ContDetails"][0]["LValue"]
                peripheral.status_code = conn_json["results"]["DataContainer"][0]["ContDetails"][1]["LValue"]
            else:
                raise RuntimeError(
                    f"An error occurred when refreshing status: {conn_status}"
                )

    def set_status(self, status_name : str, status_value : int, device_name : str) -> bool:
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

        Raise
        -------
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
            print_response=self.print_response
        )
        conn2 = connection.GetJobDoneReport(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response
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
            job_info=commander.get_b64command(status_name, status_value)
        )
        self._session_token = conn.session_token

        if not self._mqtt.mqtt_events.job.wait(timeout=10.0):
            return False
        for _ in range(self.max_retries):
            if not self._mqtt.mqtt_events.job_done_report.wait(timeout=10.0):
                self._mqtt.mqtt_events.job_done_report.clear()
                continue
            conn_status, conn_json = conn2.get_data(
                device_id=self._device_id
            )
            if conn_status == 'OK' and \
                len(conn_json['results']) != 0 and \
                conn_json['results'][0]['JobStatus'] == 0:
                if not self._mqtt.mqtt_events.peripheral.wait(timeout=10.0):
                    return False
                time.sleep(0.5) # still needs to wait a moment.
                return True
        return False


class AWSThing:
    """AWS thing (device) information.

    Parameters
    ----------
    thing_json : dict
        Thing json of specific device.
    """

    supported_device_type = {
        "1": "AC",
        "2": "DH",
        #3: "HE",
        #4: "PM25_PANEL",
    }

    def __init__(self, thing_json : dict) -> None:
        self._json = thing_json
        self._available = True
        self._shadow = None
        self._status_code = None
        self._support_code = None

    def __repr__(self) -> str:
        ret = (
            f"name: {self.name}\n"
            f"brand: {self.brand}\n"
            f"model: {self.model}\n"
            f"type: {self.type}\n"
            f"available: {self.available}\n"
            f"status_code: {self.status_code}\n"
            f"support_code: {self.support_code}\n"
            f"gateway_mac_address: {self.gateway_mac_address}"
        )
        return ret

    @classmethod
    def from_device_names(
        cls,
        things_json : dict,
        device_names : Optional[Union[List[str], str]]
    ) -> Dict[str, object]:
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

        assert device_names is None or len(device_names) == len(things), \
            "Some of device_names are not available from the API."

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
        
        return getattr(self._support_code, "Brand")

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

        return getattr(self._support_code, "Model")

    @property
    def name(self) -> str:
        """Device name.

        Returns
        -------
        str
            Device name.
        """

        return self._json['CustomDeviceName']

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
    def shadow(self, x : dict) -> None:
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
    def status_code(self, x : JciHitachiAWSStatus) -> None:
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
    def support_code(self, x : JciHitachiAWSStatusSupport) -> None:
        self._support_code = x

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
            If not supported, 'unknown' will be returned. (currently supports: `AC`, `DH`)
        """

        return self.supported_device_type.get(
            self._json['DeviceType'],
            'unknown'
        )


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
        For furture use.
    print_response : bool, optional
        If set, all responses of httpx and MQTT will be printed, by default False.
    """

    def __init__(self, 
        email : str,
        password : str,
        device_names : Optional[Union[List[str], str]] = None,
        max_retries : int = 5,
        device_offline_timeout : float = 45.0,
        print_response : bool = False
    ) -> None:
        self.email = email
        self.password = password
        self.device_names = device_names
        self.max_retries = max_retries
        self.device_offline_timeout = device_offline_timeout
        self.print_response = print_response

        self._mqtt : aws_connection.JciHitachiAWSMqttConnection = None
        self._device_id : int = random.randint(1000, 6999)
        self._things : Dict[str, AWSThing] = {}
        self._aws_tokens : aws_connection.AWSTokens = None
        self._aws_identity : aws_connection.AWSIdentity = None
        self._aws_credentials : aws_connection.AWSCredentials = None
        self._host_identity_id : str = None
        self._token_refresh_counter : int = 0
        self._task_id : int = 0

    @property
    def things(self) -> Dict[str, AWSThing]:
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
            Serial number counted from 0.
        """

        self._task_id += 1
        return self._task_id

    def _check_before_publish(self) -> None:
        # Reauthenticate 5 mins before AWSTokens or AWSCredentials expiration.
        current_time = time.time()
        if self._aws_tokens.expiration - current_time <= 300 or self._aws_credentials.expiration - current_time <= 300.0:
            self.reauth()

        if self._mqtt.mqtt_events.mqtt_error_event.is_set():
            if self._mqtt.mqtt_events.mqtt_error == "wssHandShakeError":
                self._mqtt.mqtt_events.mqtt_error_event.clear()
                self.reauth()

    def login(self) -> None:
        """Login API.

        Raises
        ------
        RuntimeError
            If a login error occurs, RuntimeError will be raised.
        """

        conn = aws_connection.GetUser(
            email=self.email,
            password=self.password,
            print_response=self.print_response,
        )
        self._aws_tokens = conn.aws_tokens
        conn_status, self._aws_identity = conn.get_data()

        conn = aws_connection.GetCredentials(
            email=self.email,
            password=self.password,
            aws_tokens=self._aws_tokens,
            print_response=self.print_response,
        )
        conn_status, self._aws_credentials = conn.get_data(self._aws_identity)

        conn = aws_connection.ListSubUser(self._aws_tokens, print_response=self.print_response)
        conn_status, conn_json = conn.get_data()

        if conn_status == "OK":
            for user in conn_json["results"]["FamilyMemberList"]:
                if user["isHost"]:
                    self._host_identity_id = user["userId"]
                    break
        else:
            raise RuntimeError(f"An error occurred when listing account users: {conn_status}")

        conn = aws_connection.GetAllDevice(self._aws_tokens, print_response=self.print_response)
        conn_status, conn_json = conn.get_data()

        if conn_status == "OK":
            # Things
            self._things = AWSThing.from_device_names(
                conn_json,
                self.device_names
            )
            self.device_names = list(self._things.keys())
            thing_names = [value.thing_name for value in self._things.values()]

            # mqtt
            self._mqtt = aws_connection.JciHitachiAWSMqttConnection(self._aws_credentials, print_response=self.print_response)
            self._mqtt.configure()
            self._mqtt.connect(self._host_identity_id, thing_names)

            # status
            self.refresh_status(refresh_support_code=True, refresh_shadow=True)
        else:
            raise RuntimeError(f"An error occurred when retrieving device info: {conn_status}")
    
    def logout(self) -> None:
        """Logout API.
        """
        
        self._mqtt.disconnect()

    def reauth(self) -> None:
        conn = aws_connection.JciHitachiAWSCognitoConnection(
            email=self.email,
            password=self.password,
            aws_tokens=self._aws_tokens,
            print_response=self.print_response,
        )
        conn_status, self._aws_tokens = conn.login(use_refresh_token=False)

        conn = aws_connection.GetCredentials(
            email=self.email,
            password=self.password,
            aws_tokens=self._aws_tokens,
            print_response=self.print_response,
        )
        conn_status, self._aws_credentials = conn.get_data(self._aws_identity)

        thing_names = [value.thing_name for value in self._things.values()]

        self._mqtt.aws_credentials = self._aws_credentials
        self._mqtt.disconnect()
        self._mqtt.configure()
        self._mqtt.connect(self._host_identity_id, thing_names)

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
            print_response=self.print_response
        )
        aws_conn_status, _ = conn.get_data(new_password)
        if aws_conn_status != "OK":
            raise RuntimeError(f"An error occurred when changing AWS Cognito password: {aws_conn_status}")

        conn = connection.UpdateUserCredential(
            self.email,
            self.password,
            print_response=self.print_response
        )
        hitachi_conn_status, _ = conn.get_data(new_password)
        if hitachi_conn_status != "OK":
            raise RuntimeError(f"An error occurred when changing Hitachi password: {hitachi_conn_status}")

    def refresh_status(self, device_name : Optional[str] = None, refresh_support_code : bool = False, refresh_shadow : bool = False) -> None:
        """Refresh device status from the API.

        Parameters
        ----------
        device_name : str, optional
            Refreshing a device's status by its name.
            If None is given, all devices' status will be refreshed,
            by default None.
        refresh_support_code : bool, optional
            Whether or not to refresh support code.
        refresh_shadow : bool, optional
            Whether or not to refresh AWS IoT Shafow.
        Raise
        -------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        self._check_before_publish()

        for name, thing in self._things.items():
            if (device_name and name != device_name) or \
                    thing.type == "unknown":
                continue

            if refresh_support_code:
                self._mqtt.publish(f"{self._host_identity_id}/{thing.thing_name}/registration/request", {"Timestamp": time.time()})
                if not self._mqtt.mqtt_events.device_support_event.wait(timeout=10.0):
                    raise RuntimeError(f"An error occurred when refreshing support code.")
                else:
                    thing.support_code = self._mqtt.mqtt_events.device_support.get(thing.thing_name)
                self._mqtt.mqtt_events.device_support_event.clear()
                time.sleep(0.5)
            if refresh_shadow:
                self._mqtt.publish_shadow(thing.thing_name, "get", shadow_name="info")
                if not self._mqtt.mqtt_events.device_shadow_event.wait(timeout=10.0):
                    raise RuntimeError(f"An error occurred when refreshing Shadow.")
                else:
                    thing.shadow = self._mqtt.mqtt_events.device_shadow.get(thing.thing_name)

            self._mqtt.publish(f"{self._host_identity_id}/{thing.thing_name}/status/request", {"Timestamp": time.time()})
            if not self._mqtt.mqtt_events.device_status_event.wait(timeout=10.0):
                raise RuntimeError(
                    f"An error occurred when refreshing status code."
                )
            else:
                thing.status_code = self._mqtt.mqtt_events.device_status.get(thing.thing_name)
            self._mqtt.mqtt_events.device_status_event.clear()

    def get_status(self, device_name: Optional[str] = None, legacy=False) -> Dict[str, JciHitachiAWSStatus]:
        """Get device status after refreshing status.

        Parameters
        ----------
        device_name : str, optional
            Getting a device's status by its name.
            If None is given, all devices' status will be returned,
            by default None.
        legacy : bool, optional
            Whether or not to return legacy (old) status class.

        Returns
        -------
        dict of JciHitachiAWSStatus or JciHitachiStatus.
            if legacy is True, return a dict of JciHitachiStatus; otherwise, return a dict of JciHitachiAWSStatus instances.
        """
        
        statuses = {}
        for name, thing in self._things.items():
            if (device_name and name != device_name) or \
                    thing.type == "unknown":
                continue
            if legacy:
                statuses[name] = thing.status_code.legacy_status_class
            else:
                statuses[name] = thing.status_code
        return statuses

    def set_status(self, status_name: str, status_value: int, device_name: str) -> bool:
        """Set status to a thing.

        Parameters
        ----------
        status_name : str
            Status name.
        status_value : int
            Status value.
        device_name : str
            Device name.

        Returns
        -------
        bool
            Return True if the command has been successfully executed. Otherwise, return False.

        Raise
        -------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        self._check_before_publish()

        thing = self._things[device_name]
        if status_name not in JciHitachiAWSStatus.compability_mapping[thing.type]:
            status_name = JciHitachiAWSStatus.convert_old_to_new(thing.type, status_name)
        shadow_publish_mapping = {
            "CleanFilterNotification": "filter",
            "CleanNotification": "filter",
        }
        

        #if status_name in shadow_publish_mapping:
        if False: # block going into this # FIXME: Fix this.
            shadow_publish_schema = {
                "filter": {  
                    status_name: True,
                    "FilterElapsedHour": 0 if status_value == 0 else 500,
                }
            }
            self._mqtt.publish_shadow(
                thing.thing_name, 
                "update", 
                {
                    "state": {
                        "desired": {
                            **shadow_publish_schema[shadow_publish_mapping[status_name]]
                        }
                    }
                },
                shadow_name="info"
            )
            if not self._mqtt.mqtt_events.device_control_event.wait(timeout=10.0):
                device_control = None
            else:
                device_control = self._mqtt.mqtt_events.device_control.get(thing.thing_name)
                #if device_control["state"]["reported"][status_name] == bool(status_value):
                return True
            return False

        self._mqtt.publish(f"{self._host_identity_id}/{thing.thing_name}/control/request", {
            "Condition": {
                "ThingName": thing.thing_name,
                "Index": 0,
                "Geofencing": {
                    "Arrive": None,
                    "Leave": None,
                },
            },
            status_name: status_value,
            "TaskID": self.task_id,
            "Timestamp": time.time(),
        })

        for _ in range(self.max_retries):
            if not self._mqtt.mqtt_events.device_control_event.wait(timeout=10.0):
                device_control = None
            else:
                device_control = self._mqtt.mqtt_events.device_control.get(thing.thing_name)
                if device_control.get(status_name) == status_value:
                    self._mqtt.mqtt_events.device_control_event.clear()
                    time.sleep(0.5)
                    return True
            time.sleep(0.5)
        return False