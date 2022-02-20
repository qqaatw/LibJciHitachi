from JciHitachi.api import JciHitachiAWSAPI

# Fill out your Jci Hitachi email address, password, and device name.
EMAIL = "yourname@yourdomain.com"
PASSWORD = "password"
DEVICENAME = "living room"

# Login
api = JciHitachiAWSAPI(EMAIL, PASSWORD, DEVICENAME)
api.login()

# Check device status 
# device_status = api.get_status(legacy=True) # return legacy status class
device_status = api.get_status()
print(device_status[DEVICENAME].status)

# Set device status 
# For available command names and values, please refer to
# model.py->JciHitachiAWSStatus.compatibility_mapping
if api.set_status('TemperatureSetting', 27, DEVICENAME):
    print('Success')
else:
    print('Failed')

# Check the updated device status
api.refresh_status()
device_status = api.get_status()
print(device_status[DEVICENAME].status)