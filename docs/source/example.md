# Example

## API

1. Import API and define credential information.

    ```
    from JciHitachi.api import JciHitachiAWSAPI

    # Fill out your Jci Hitachi email address, password, and device name.
    EMAIL = "yourname@yourdomain.com"
    PASSWORD = "password"
    DEVICENAME = "living room"
    ```

2. Login API and get current status.

    ```
    # Login
    api = JciHitachiAWSAPI(EMAIL, PASSWORD, DEVICENAME)
    api.login()

    # Check device status
    # device_status = api.get_status(legacy=True) # return legacy status class
    device_status = api.get_status()
    print(device_status[DEVICENAME].status)
    ```

3. Set a new status to a device.

    ```
    # Set device status
    # For available command names and values, please refer to
    # model.py->STATUS_DICT
    if api.set_status(status_name='TemperatureSetting', device_name=DEVICENAME, status_value=27):
        print('Success')
    else:
        print('Failed')
    ```

4. Check the updated status.

    ```
    # Check the updated device status
    api.refresh_status()
    device_status = api.get_status()
    print(device_status[DEVICENAME].status)
    ```

The python script can be found [here](https://github.com/qqaatw/LibJciHitachi/blob/master/example.py).

## Legacy API

1. Import API and define credential information.

    ```
    from JciHitachi.api import JciHitachiAPI

    # Fill out your Jci Hitachi email address, password, and device name.
    EMAIL = "yourname@yourdomain.com"
    PASSWORD = "password"
    DEVICENAME = "living room"
    ```

2. Login API and get current status.

    ```
    # Login
    api = JciHitachiAPI(EMAIL, PASSWORD, DEVICENAME)
    api.login()

    # Check device status
    device_status = api.get_status()
    print(device_status[DEVICENAME].status)
    ```

3. Set a new status to a device.

    ```
    # Set device status
    # For available command names and values, please refer to
    # Air conditioner: model.py->JciHitachiAC
    # Dehumidifier: model.py->JciHitachiDH
    if api.set_status('target_temp', 27, DEVICENAME):
        print('Success')
    else:
        print('Failed')
    ```

4. Check the updated status.

    ```
    # Check the updated device status
    api.refresh_status()
    device_status = api.get_status()
    print(device_status[DEVICENAME].status)
    ```

The python script can be found [here](https://github.com/qqaatw/LibJciHitachi/blob/master/legacy_example.py).