import time

from JciHitachi.api import JciHitachiAPI

# Fill out your Jci Hitachi email address, password, and device name.
api = JciHitachiAPI("yourname@yourdomain.com", "yourpassword", "devicename", device_type="AC")
api.login()

# Check device status 
ac_status = api.get_status()
print(ac_status.status)

# Set device status
if api.set_status('target_temp', 27):
    print('Success')
else:
    print('Failed')

# Check the updated device status
time.sleep(2) # wait a moment for update.
api.refresh_status()
ac_status = api.get_status()
print(ac_status.status)