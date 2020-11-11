from . import connection
from .status import JciHitachiStatusInterpreter, JciHitachiAC

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
    device_type : str
        Device type. Currently available types: AC.
    print_response : bool
        If set, all responses of requests will be printed, by default False.
    """

    def __init__(self, email, password, device_name, device_type="AC", print_response=False):
        self.email = email
        self.password = password
        self.device_name = device_name
        self.device_type = device_type
        self.print_response = print_response

        self._code = None

    def login(self):
        """Login API.

        Raises
        ------
        RuntimeError
            If a login error occurs, RuntimeError will be raised.
        """

        peripherals = connection.GetPeripheralsByUser(self.email, self.password, print_response=self.print_response)
        comm_status, peripherals_json = peripherals.get_data()

        if comm_status == "OK":
            dev_idx = [res["DeviceName"] for res in peripherals_json["results"]].index(self.device_name)
            container = connection.GetDataContainerByID(None, None, session_token=peripherals.session_token, print_response=self.print_response)
            comm_status, container_json = container.get_data(peripherals_json["results"][dev_idx])
            self._code = container_json["results"]["DataContainer"][0]["ContDetails"][1]["LValue"]
            
        else:
            raise RuntimeError("Error: {}.".format(comm_status))
    
    def get_status(self):
        """Get device status.

        Returns
        -------
        JciHitachi status instance.
            Return status instance according to device type.
            For example, if device type is `AC`, then return JciHitachiAC.

        Raises
        ------
        ValueError
            When unsupported device type is given, ValueError will be raised.
        """

        dev_status = JciHitachiStatusInterpreter(self._code).decode_status()
        if self.device_type == "AC":
            return JciHitachiAC(dev_status)
        else:
            raise ValueError("Unsupported device type.")

