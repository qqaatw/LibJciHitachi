from JciHitachi.api import JciHitachiAPI


# Fill out your Jci Hitachi email address, password, and device name.
EMAIL = "yourname@yourdomain.com"
PASSWORD = "password"
DEVICENAME = "living room"

# Login
api = JciHitachiAPI(EMAIL, PASSWORD, DEVICENAME)
api.login()

# Check device status
device_status = api.get_status()
print(device_status[DEVICENAME].status)

# Set device status
# For available command names and values, please refer to
# Air conditioner: status.py->JciHitachiAC
# Dehumidifier: status.py->JciHitachiDH
if api.set_status("target_temp", 27, DEVICENAME):
    print("Success")
else:
    print("Failed")

# Check the updated device status
api.refresh_status()
device_status = api.get_status()
print(device_status[DEVICENAME].status)
