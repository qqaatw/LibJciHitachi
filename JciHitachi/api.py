import random
import time

from . import connection
from .status import JciHitachiStatusInterpreter, JciHitachiAC, JciHitachiCommandAC


class Peripherals:
    """Peripherals (Devices) Information.

    Parameters
    ----------
    peripherals_json : dict
        Json from GetPeripheralsByUser.
    device_name : str
        Device name.
    """

    def __init__(self, peripherals_json, device_name):
        self._json = peripherals_json
        self._device_idx = [res["DeviceName"] for res in peripherals_json["results"]].index(device_name)
        self._gateway_id = peripherals_json["results"][self._device_idx]["ObjectID"]
        self._gateway_mac_address = peripherals_json["results"][self._device_idx]["GMACAddress"]
        self._task_id = 0

    @property
    def device_idx(self):
        """Device index of self._json.

        Returns
        -------
        int
            Device index.
        """

        return self._device_idx

    @property
    def gateway_id(self):
        """Gateway ID.

        Returns
        -------
        int
            Gateway ID.
        """

        return self._gateway_id
    
    @property
    def gateway_mac_address(self):
        """Gateway mac address.

        Returns
        -------
        str
            Gateway mac address.
        """
        return self._gateway_mac_address

    @property
    def task_id(self):
        """Task ID.

        Returns
        -------
        int
            Serial number counted from 0.
        """

        self._task_id += 1
        return self._task_id
    
    @property
    def picked_peripheral(self):
        """Picked peripheral.

        Returns
        -------
        dict
            Picked peripheral.
        """

        return self._json["results"][self._device_idx]


class JciHitachiAPI:
    """Jci-Hitachi API.

    Parameters
    ----------

    email : str
        User email.
    password : str
        User password.
    device_name : str
        Device name.
    device_type : str, optional
        Device type, by default AC. Currently available types: AC.
    max_retries : int, optional
        Maximum number of retries when setting status, by default 5.
    print_response : bool
        If set, all responses of requests will be printed, by default False.
    """

    def __init__(self, email, password, device_name, device_type="AC", max_retries=5, print_response=False):
        self.email = email
        self.password = password
        self.device_name = device_name
        self.device_type = device_type
        self.max_retries = max_retries
        self.print_response = print_response

        self._code = None
        self._device_id = random.randint(1000, 6999)
        self._session_token = None
        self._peripherals = None

        assert self.device_type in ["AC"], \
            "The specified device is currently unsupported: {}".format(device_type)

    def login(self):
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
            if self.device_name is not None:
                self._peripherals = Peripherals(peripherals_json, self.device_name)
                self.refresh_status()
        else:
            raise RuntimeError("Error: {}.".format(comm_status))
    
    def change_password(self, new_password):
        """Change password.

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

    def get_status(self):
        """Get device status.

        Returns
        -------
        JciHitachi status instance.
            Return status instance according to device type.
            For example, if the device type is `AC`, then return JciHitachiAC instance.

        Raises
        ------
        ValueError
            When an unsupported device type is given, ValueError will be raised.
        """

        dev_status = JciHitachiStatusInterpreter(self._code).decode_status()
        
        if self.device_type == "AC":
            return JciHitachiAC(dev_status)

    def refresh_status(self):
        """Refresh device status from the API.
        """

        container = connection.GetDataContainerByID(
            None,
            None,
            session_token=self._session_token,
            print_response=self.print_response
        )
        comm_status, container_json = container.get_data(
            self._peripherals.picked_peripheral
        )

        self._code = container_json["results"]["DataContainer"][0]["ContDetails"][1]["LValue"]

    def set_status(self, status_name, status_value):
        """Set status of a peripheral.

        Parameters
        ----------
        status_name : str
            Status name, which has to be in idx dict. Eg. JciHitachiAC.idx
        status_value : int
            Status value.

        Returns
        -------
        bool
            Return True if the status has been successfully executed. Otherwise, return False.
        
        Raise
        -------
        RuntimeError
            If an error occurs, RuntimeError will be raised.
        """

        if self.device_type == "AC":
            commander = JciHitachiCommandAC(
                self._peripherals.gateway_mac_address)

        job = connection.CreateJob(
            None,
            None,
            session_token=self._session_token,
            print_response=self.print_response
        )
        comm_status, job_json = job.get_data(
            gateway_id=self._peripherals.gateway_id,
            device_id=self._device_id,
            task_id=self._peripherals.task_id,
            job_info=commander.get_b64command(status_name, status_value)
        )
        
        for t in range(self.max_retries):
            time.sleep(1)
            job_report = connection.GetJobDoneReport(
                None,
                None,
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
                    return True
        return False
