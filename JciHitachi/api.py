import random
import time
from typing import Dict, List, Optional, Union

from . import connection
from .status import JciHitachiCommand, JciHitachiCommandAC, JciHitachiStatusInterpreter
from .model import JciHitachiACSupport, JciHitachiStatus, JciHitachiAC


class Peripheral:
    """Peripheral (Device) Information.

    Parameters
    ----------
    peripheral_json : dict
        Peripheral json of specific device.
    """

    supported_device_type = {
        144: "AC",
        #146: "DH"
        #148: "HE"
    }

    def __init__(self, peripheral_json : dict) -> None:
        self._json = peripheral_json
        self._status_code = ""
        self._support_code = ""

    def __repr__(self) -> str:
        ret = f"name: {self.name}\n" + \
              f"type: {self.type}\n" + \
              f"status_code: {self.status_code}\n" + \
              f"gateway_id: {self.gateway_id}\n" + \
              f"gateway_mac_address: {self.gateway_mac_address}"
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
    def commander(self) -> Union[JciHitachiCommand, None]:
        """Return a new JciHitachiCommand instance based on peripheral's type.

        Returns
        -------
        JciHitachiCommand or None
            JciHitachiCommand instance.
        """

        if self.type == "AC":
            return JciHitachiCommandAC(self.gateway_mac_address)
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

    @property
    def type(self) -> str:
        """Device type.

        Returns
        -------
        str
            Device type. 
            If not supported, 'unknown' will be returned. (Currently available: `AC`)
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
    print_response : bool, optional
        If set, all responses of requests will be printed, by default False.
    """

    def __init__(self, 
        email : str,
        password : str,
        device_names : Optional[Union[List[str], str]] = None,
        max_retries : int = 5,
        print_response: bool = False
    ) -> None:
        self.email = email
        self.password = password
        self.device_names = device_names
        self.max_retries = max_retries
        self.print_response = print_response

        self._device_id = random.randint(1000, 6999)
        self._peripherals = {}
        self._session_token = None
        self._task_id = 0

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
    def task_id(self) -> int:
        """Task ID.

        Returns
        -------
        int
            Serial number counted from 0.
        """

        self._task_id += 1
        return self._task_id

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
            self._peripherals = Peripheral.from_device_names(
                conn_json,
                self.device_names
            )
            self.device_names = list(self._peripherals.keys())

            self.refresh_status()
        else:
            raise RuntimeError(
                f"An error occurred when API login: {conn_status}.")

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

        status = {}
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            dev_status = JciHitachiStatusInterpreter(
                peripheral.status_code
            ).decode_status()

            if peripheral.type == "AC":
                status[name] = JciHitachiAC(dev_status)
        return status
    
    def get_supported_status(self, device_name: Optional[str] = None) -> Dict[str, JciHitachiStatus]:
        """Get supported device status after refreshing status.

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
            For example, if the device type is `AC`, then return JciHitachiACSupport instance.
        """

        supported_status = {}
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            dev_status = JciHitachiStatusInterpreter(
                peripheral.support_code,
                True
            ).decode_support()

            if peripheral.type == "AC":
                supported_status[name] = JciHitachiACSupport(dev_status)
        return supported_status

    def refresh_status(self, device_name : Optional[str] = None) -> None:
        """Refresh device status from the API.

        Parameters
        ----------
        device_name : str, optional
            Refreshing a device's status by its name.
            If None is given, all devices' status will be refreshed,
            by default None.
        """

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
                self._peripherals[name].support_code = conn_json["results"]["DataContainer"][0]["ContDetails"][0]["LValue"]
                self._peripherals[name].status_code = conn_json["results"]["DataContainer"][0]["ContDetails"][1]["LValue"]
            else:
                raise RuntimeError(
                    f"An error occurred when refreshing status: {conn_status}")

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

        commander = self._peripherals[device_name].commander

        conn = connection.CreateJob(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response
        )
        conn_status, conn_json = conn.get_data(
            gateway_id=self._peripherals[device_name].gateway_id,
            device_id=self._device_id,
            task_id=self.task_id,
            job_info=commander.get_b64command(status_name, status_value)
        )
        self._session_token = conn.session_token

        for _ in range(self.max_retries):
            time.sleep(0.8)
            conn = connection.GetJobDoneReport(
                self.email,
                self.password,
                session_token=self._session_token,
                print_response=self.print_response
            )
            conn_status, conn_json = conn.get_data(
                device_id=self._device_id
            )
            if conn_status == 'OK' and len(conn_json['results']) != 0:
                if conn_json['results'][0]['JobStatus'] == 0:
                    #code = conn_json['results'][0]['ReportedData']
                    #reported_status = JciHitachiStatusInterpreter(code).decode_status()
                    #assert reported_status.get(status_name) == status_value, \
                    #    "The Reported status value is not the same as status_value."

                    # The API seems to be delayed to update status, so wait for 1.5 sec.
                    time.sleep(1.5)
                    return True
        return False
