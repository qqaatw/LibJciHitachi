import json
import requests

from .utility import convert_hash

API_ENDPOINT = "https://api.jci-hitachi-smarthome.com/3.6/"
API_ID = "ODM-HITACHI-APP-168d7d31bbd2b7cbbd"
API_KEY = "23f26d38921dda92c1c2939e733bca5e"

APP_PLATFORM = 2  # 1=IOS 2=Android
APP_VERSION = "3.50.500"

class JciHitachiConnection:
    """Connecting to Jci-Hitachi API to get data or send commands.

    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    session_token : str, optional
        If session_token is given, it is used by request, 
        otherwise perform a login procedure to obtain a new token,
        by default None.
    proxy : str, optional
        Proxy setting. Format:"IP:port", by default None. 
    print_response : bool, optional
        If set, all responses of requests will be printed, by default False.
    """
    
    def __init__(self, email, password, session_token=None, proxy=None, print_response=False):
        self._login_response = None
        self._email = email
        self._password = password
        self._print_response = print_response

        if session_token:
            self._session_token = session_token
        else:
            self._session_token = None
            self.login()
        
        self._proxies = {'http': proxy, 'https': proxy} if proxy else None
    
    @property
    def logged(self):
        return True if self._session_token is not None else False

    @property
    def session_token(self):
        return self._session_token

    def _generate_normal_headers(self):
        normal_headers = {
            "X-DK-Application-Id" : API_ID,
            "X-DK-API-Key" : API_KEY,
            "X-DK-Session-Token" : self._session_token, 
            "User-Agent": "Dalvik/2.1.0",
            "content-type" : "application/json",
            "Accept" : "application/json"
        }
        return normal_headers

    def _handle_response(self, response):
        response_json = response.json()
        code = response_json["status"]["code"]
        if code == 0:
            return code, "OK", response_json
        elif code == 6:
            return code, "Invalid email or password", response_json
        elif code == 12:
            return code, "Invalid session token", response_json
        else:
            return code, "Unknown error", response_json

    def _send(self, api_name, json=None):
        code = 12
        while code == 12:
            req = requests.post(
                "{}{}".format(API_ENDPOINT, api_name),
                headers=self._generate_normal_headers(),
                json=json,
                verify=False,
                proxies=self._proxies
            )
            if self._print_response:
                self.print_response(req)

            code, message, response_json = self._handle_response(req)
            
            if code == 12:
                if not self.login():
                    break

        return message, response_json

    def login(self):
        login_json_data = {
            "ServerLogin": {
                "Email": self._email,
                "HashCode": f"{self._email}{convert_hash(f'{self._email}{self._password}')}"
            },
            "AppVersion": {
                "Platform": int(APP_PLATFORM),
                "Version": APP_VERSION
            }
        }

        login_headers = {
            "X-DK-Application-Id" : API_ID,
            "X-DK-API-Key" : API_KEY,
            "content-type" : "application/json",
            "Accept" : "application/json"
        }

        login_req = requests.post("{}{}".format(API_ENDPOINT, "UserLogin.php"), 
            json=login_json_data,
            headers=login_headers,
            verify=False
        )

        if self._print_response:
            self.print_response(login_req)

        if login_req.status_code == requests.codes.ok:
            code, message, self._login_response = self._handle_response(login_req)
            if message == "OK":
                self._session_token = self._login_response["results"]["sessionToken"]
                return True
                
        return False

    def get_data(self):
        raise NotImplementedError

    def print_response(self, response):
        print('===================================================')
        print(self.__class__.__name__, 'Response:')
        print('headers:', response.headers)
        print('status_code:', response.status_code)
        print('text:', json.dumps(response.json(), indent=True))
        print('===================================================')


class RegisterMobileDevice(JciHitachiConnection):
    """API internal endpoint. (Unused)
    
    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)

    def get_data(self, device_token):
        json_data = {
            "DeviceType": APP_PLATFORM,
            "DeviceToken": device_token
        }

        return self._send("RegisterMobileDevice.php", json_data)


class UpdateUserCredential(JciHitachiConnection):
    """API internal endpoint. (Tested)
    
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
            "ServerLogin": {
                "OldEmail": self._email,
                "OldPassword": convert_hash(f'{self._email}{self._password}'),
                "NewPassword": convert_hash(f'{self._email}{new_password}'),
            }
        }

        return self._send("UpdateUserCredential.php", json_data)


class GetServerLastUpdateInfo(JciHitachiConnection):
    """API internal endpoint. (Unused)
    
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
        return self._send("GetServerLastUpdateInfo.php")


class GetPeripheralsByUser(JciHitachiConnection):
    """API internal endpoint. (Tested)
    
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
        return self._send("GetPeripheralsByUser.php")


class GetDataContainerByID(JciHitachiConnection):
    """API internal endpoint. (Tested)
    
    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self, picked_peripheral_json):
        ContMID = picked_peripheral_json["Peripherals"][0]["DataContainer"][0]["ContMID"]
        ContDID_1 = picked_peripheral_json["Peripherals"][0]["DataContainer"][0]["ContDetails"][0]["ContDID"]
        ContDID_2 = picked_peripheral_json["Peripherals"][0]["DataContainer"][0]["ContDetails"][1]["ContDID"]

        json_data = {
            "Format": 0,
            "DataContainer": [
                {"ContMID" : ContMID,
                 "ContDetails":   
                    [
                        {"ContDID": ContDID_1},
                        {"ContDID": ContDID_2}
                    ]
                }       
            ]
        }

        return self._send("GetDataContainerByID.php", json_data)


class GetPeripheralByGMACAddress(JciHitachiConnection):
    """API internal endpoint. (Unused)
    
    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self, peripheral_json):
        GMACAddress = peripheral_json["results"][0]["GMACAddress"]
        json_data = {
            "Data" : [
                {"GMACAddress": GMACAddress}
            ]
        }

        return self._send("GetPeripheralByGMACAddress.php", json_data)


class CreateJob(JciHitachiConnection):
    """API internal endpoint. (Tested)
    
    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self, gateway_id, device_id, task_id, job_info):
        json_data = {
            "Data": [
                {
                    "GatewayID": gateway_id,
                    "DeviceID": device_id, # random device ID
                    "TaskID": task_id, # serial number started from 1
                    "JobInformation": job_info
                }
            ]
        }

        return self._send("CreateJob.php", json_data)


class GetJobDoneReport(JciHitachiConnection):
    """API internal endpoint. (Tested)
    
    Parameters
    ----------
    email : str
        User email.
    password : str
        User password.
    """

    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)

    def get_data(self, device_id):
        json_data = {
            "DeviceID": device_id
        }

        return self._send("GetJobDoneReport.php", json_data)
