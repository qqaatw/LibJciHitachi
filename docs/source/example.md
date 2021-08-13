# Example

1. Import API and define credential informaiton. 

    ```
    from JciHitachi.api import JciHitachiAPI

    # Fill out your Jci Hitachi email address, password, and device name.
    EMAIL = "yourname@yourdomain.com"
    PASSWORD = "password"
    DEVICENAME = "living room"
    ```

2. Login to API and get current status.

    ```
    api = JciHitachiAPI(EMAIL, PASSWORD, DEVICENAME)
    api.login()

    # Check device status 
    ac_status = api.get_status()
    print(ac_status[DEVICENAME].status)
    ```

3. Set a new status to a device.
    
    ```
    # Set device status 
    # For available command names and values, please refer to status.py->JciHitachiAC
    if api.set_status('target_temp', 27, DEVICENAME):
        print('Success')
    else:
        print('Failed')
    ```

4. Check the updated status.
    
    ```
    # Check the updated device status
    api.refresh_status()
    ac_status = api.get_status()
    print(ac_status[DEVICENAME].status)
    ```

The python script can be found [here](https://github.com/qqaatw/LibJciHitachi/blob/master/example.py).