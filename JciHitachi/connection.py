import json
import requests

from .utility import convert_hash

API_ENDPOINT = "https://api.jci-hitachi-smarthome.com/3.6/"
API_ID = "ODM-HITACHI-APP-168d7d31bbd2b7cbbd"
API_KEY = "23f26d38921dda92c1c2939e733bca5e"

APP_PLATFORM = 2
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
    print_response : bool, optional
        If set, all responses of requests will be printed, by default False.
    """
    
    def __init__(self, email, password, session_token=None, print_response=False):
        self._login_response = None
        self._email = email
        self._password = password
        self._print_response = print_response

        if session_token:
            self._session_token = session_token
        else:
            self._session_token = None
            self.login()
    
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
            "content-type" : "application/json",
            "Accept" : "application/json"
        }
        return normal_headers

    def _handle_response(self, response):
        response_json = response.json()
        code = response_json["status"]["code"]
        if code == 0:
            return "OK", response_json
        elif code == 6:
            return "Invalid email or password", response_json
        elif code == 12:
            return "Invalid session token", response_json
        else:
            return "Unknown error", response_json

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
            self.print_response('Login', login_req)

        if login_req.status_code == requests.codes.ok:
            status, self._login_response = self._handle_response(login_req)
            if status == "OK":
                self._session_token = self._login_response["results"]["sessionToken"]
                return True
                
        return False

    def get_data(self):
        raise NotImplementedError

    def print_response(self, name, response):
        print(name , ' Response:')
        print('headers:', response.headers)
        print('status_code:', response.status_code)
        print('text:', json.dumps(response.json(), indent=True))


class GetServerLastUpdateInfo(JciHitachiConnection):
    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)

    def get_data(self):       
        req = requests.post("{}{}".format(API_ENDPOINT, "GetServerLastUpdateInfo.php"), 
            headers=self._generate_normal_headers(),
            verify=False
        )
        if self._print_response:
            self.print_response(self.__class__.__name__, req)
        
        return self._handle_response(req)


class GetPeripheralsByUser(JciHitachiConnection):
    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self):  
        req = requests.post("{}{}".format(API_ENDPOINT, "GetPeripheralsByUser"),
            headers=self._generate_normal_headers(),
            verify=False
        )
        if self._print_response:
            self.print_response(self.__class__.__name__, req)

        return self._handle_response(req)        


class GetDataContainerByID(JciHitachiConnection):
    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self, picked_peripheral_json):      
        ContMID = picked_peripheral_json["Peripherals"][0]["DataContainer"][0]["ContMID"]
        ContDID_1 = picked_peripheral_json["Peripherals"][0]["DataContainer"][0]["ContDetails"][0]["ContDID"]
        ContDID_2 = picked_peripheral_json["Peripherals"][0]["DataContainer"][0]["ContDetails"][1]["ContDID"]

        get_container_json_data = {
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
        req = requests.post("{}{}".format(API_ENDPOINT, "GetDataContainerByID"),
            headers=self._generate_normal_headers(),
            json=get_container_json_data,
            verify=False
        )
        if self._print_response:
            self.print_response(self.__class__.__name__, req)

        return self._handle_response(req)


class GetPeripheralByGMACAddress(JciHitachiConnection):
    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self, peripheral_json):
        GMACAddress = peripheral_json["results"][0]["GMACAddress"]
        json_data = {
            "Data" : [
                {"GMACAddress": GMACAddress}
            ]
        }
        req = requests.post("{}{}".format(API_ENDPOINT, self.__class__.__name__),
            headers=self._generate_normal_headers(),
            json=json_data,
            verify=False
        )
        if self._print_response:
            self.print_response(self.__class__.__name__, req)
        
        return self._handle_response(req)


class CreateJob(JciHitachiConnection):
    def __init__(self, email, password, **kwargs):
        super().__init__(email, password, **kwargs)
    
    def get_data(self, return_json=True):
        json_data = {
            "Data": [
                {"GatewayID": "",
                "DeviceID": "3284SH89573", # random device ID
                "TaskID":"",
                "JobInformation": ""
                }
            ]
        }