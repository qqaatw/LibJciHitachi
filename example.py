from JciHitachi.api import JciHitachiAPI

api = JciHitachiAPI("yourname@yourdomain.com", "yourpassword", "devicename")
api.login()

ac_status = api.get_status()
print(ac_status.status)