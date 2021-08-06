import random
import time
from typing import Dict, List, Optional, Union

from . import connection
from .status import JciHitachiCommand, JciHitachiCommandAC, JciHitachiStatusInterpreter, JciHitachiAC


class Peripheral:
    """Peripheral (Device) Information.

    Parameters
    ----------
    peripheral_json : dict
        Peripheral json of specific device.
    """

    supported_device_type = {
        144: "AC"
    }

    def __init__(self, peripheral_json : dict) -> None:
        self._json = peripheral_json
        self._code = ""

    def __repr__(self) -> str:
        ret = f"name: {self.name}\n" + \
              f"type: {self.type}\n" + \
              f"code: {self.code}\n" + \
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

        for res in peripherals_json["results"]:
            if device_names is None or \
                    (device_names and res["DeviceName"] in device_names):
                if res["Peripherals"][0]["DeviceType"] in Peripheral.supported_device_type:
                    peripherals[res["DeviceName"]] = cls(res)

        assert device_names is None or len(device_names) == len(peripherals), \
            "Some of device_names are not available from the API."

        return peripherals

    @property
    def code(self) -> str:
        """Peripheral's status code (LValue) reported by the API.

        Returns
        -------
        str
            Status code.
        """

        return self._code

    @code.setter
    def code(self, x : str) -> None:
        self._code = x

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
    def type(self) -> str:
        """Device type.

        Returns
        -------
        str
            Device type. 
            If not supported, 'unknown' will be returned. (Currently available: `AC`)
        """

        return Peripheral.supported_device_type.get(
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

        peripherals = connection.GetPeripheralsByUser(
            self.email,
            self.password,
            print_response=self.print_response)
        comm_status, peripherals_json = peripherals.get_data()

        if comm_status == "OK":
            self._session_token = peripherals.session_token

            self._peripherals = Peripheral.from_device_names(
                peripherals_json,
                self.device_names
            )
            self.device_names = list(self._peripherals.keys())

            self.refresh_status()
        else:
            raise RuntimeError("Error: {}.".format(comm_status))

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

    def get_status(self, device_name : Optional[str] = None) -> dict:
        """Get device status after refreshing status.

        Parameters
        ----------
        device_name : str, optional
            Getting a device's status by its name.
            If None is given, all devices' status will be returned,
            by default None.

        Returns
        -------
        dict of JciHitachi status instances.
            Return a list of status instances according to device type.
            For example, if the device type is `AC`, then return JciHitachiAC instance.
        """

        statuses = {}
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            dev_status = JciHitachiStatusInterpreter(peripheral.code).decode_status()

            if peripheral.type == "AC":
                statuses[name] = JciHitachiAC(dev_status)
        return statuses

    def refresh_status(self, device_name : Optional[str] = None) -> None:
        """Refresh device status from the API.

        Parameters
        ----------
        device_name : str, optional
            Refreshing a device's status by its name.
            If None is given, all devices' status will be refreshed,
            by default None.
        """

        container = connection.GetDataContainerByID(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response
        )
        for name, peripheral in self._peripherals.items():
            if (device_name and name != device_name) or \
                    peripheral.type == "unknown":
                continue
            comm_status, container_json = container.get_data(
                peripheral.picked_peripheral
            )
            self._peripherals[name].code = container_json["results"]["DataContainer"][0]["ContDetails"][1]["LValue"]

    def set_status(self, status_name : str, status_value : int, device_name : str) -> bool:
        """Set status to a peripheral.

        Parameters
        ----------
        status_name : str
            Status name, which has to be in idx dict. Eg. JciHitachiAC.idx
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

        job = connection.CreateJob(
            self.email,
            self.password,
            session_token=self._session_token,
            print_response=self.print_response
        )
        comm_status, job_json = job.get_data(
            gateway_id=self._peripherals[device_name].gateway_id,
            device_id=self._device_id,
            task_id=self.task_id,
            job_info=commander.get_b64command(status_name, status_value)
        )

        for t in range(self.max_retries):
            time.sleep(0.8)
            job_report = connection.GetJobDoneReport(
                self.email,
                self.password,
                session_token=self._session_token,
                print_response=self.print_response
            )
            comm_status, job_report_json = job_report.get_data(
                device_id=self._device_id
            )
            if comm_status == 'OK' and len(job_report_json['results']) != 0:
                if job_report_json['results'][0]['JobStatus'] == 0:
                    #code = job_report_json['results'][0]['ReportedData']
                    #reported_status = JciHitachiStatusInterpreter(code).decode_status()
                    #assert reported_status.get(status_name) == status_value, \
                    #    "The Reported status value is not the same as status_value."

                    # The API seems to be delayed to update status, so wait for 1.5 sec.
                    time.sleep(1.5)
                    return True
        return False
