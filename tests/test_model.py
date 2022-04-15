from JciHitachi.api import AWSThing
from JciHitachi.model import STATUS_DICT, JciHitachiAWSStatus


class TestStatusDict:
    device_types = AWSThing.supported_device_type.values()
    
    def test_sanity(self):    
        attribute_keys = {"controlable", "is_numeric", "legacy_name"}

        for device_type in self.device_types:
            for status_name, status_attributes in STATUS_DICT[device_type].items():
                # Test if attribute keys are in status attributes.
                assert len(attribute_keys - set(status_attributes)) == 0, \
                    f"Lack of attribute keys: {status_name} {set(status_attributes)}"
                # Test is_numeric and id2str mutual exclusiveness
                assert status_attributes["is_numeric"] ^ ("id2str" in status_attributes), \
                    f"is_numeric and id2str are mutually exclusive: {status_name}"
        
class TestModel:
    def test_correctness(self):
        raw_ac_status = {
            'DeviceType': 1,
            'Switch': 0,
            'Mode': 0,
            'FanSpeed': 3,
            'TemperatureSetting': 26,
            'IndoorTemperature': 23,
            'SleepModeRemainingTime': 0,
            'MildewProof': 0,
            'QuickMode': 0,
            'PowerSaving': 0,
            'ControlTone': 0,
            'PowerConsumption': 5,
            'TaiseiaError': 0,
            'FilterElapsedHour': 800,
            'CleanSwitch': 0,
            'CleanNotification': 0,
            'CleanStatus': 0,
            'Error': 0,
            'RequestTimestamp': 1648618952,
            'Timestamp': 1648618953
        }
        processed_ac_status = {
            'CleanNotification': 0,
            'CleanStatus': 0,
            'CleanSwitch': 'off',
            'ControlTone': 'enabled',
            'DeviceType': 'AC',
            'Error': 0,
            'FanSpeed': 'moderate',
            'FilterElapsedHour': 800,
            'IndoorTemperature': 23,
            'MildewProof': 'disabled',
            'Mode': 'cool',
            'PowerConsumption': 0.5,
            'PowerSaving': 'disabled',
            'QuickMode': 'disabled',
            'SleepModeRemainingTime': 0,
            'Switch': 'off',
            'TaiseiaError': 0,
            'TemperatureSetting': 26,
            'max_temp': 32,
            'min_temp': 16
        }
        status = JciHitachiAWSStatus(raw_ac_status)

        assert status.status == processed_ac_status
        assert len(processed_ac_status) == len(raw_ac_status)