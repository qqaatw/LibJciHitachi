import time

from JciHitachi.api import JciHitachiAPI

# Fill out your Jci Hitachi email address, password, and device name.
EMAIL = "yourname@yourdomain.com"
PASSWORD = "password"
DEVICENAME = "living room"

api = JciHitachiAPI(EMAIL, PASSWORD, DEVICENAME)
api.login()

# Check device status 
ac_status = api.get_status()
print(ac_status[DEVICENAME].status)

# Set device status 
# For available command names and values, 
# please refer to status.py->JciHitachiAC
if api.set_status('target_temp', 27, DEVICENAME):
    print('Success')
else:
    print('Failed')

# Check the updated device status
time.sleep(2) # wait a moment for update.
api.refresh_status()
ac_status = api.get_status()
print(ac_status[DEVICENAME].status)