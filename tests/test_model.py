from JciHitachi.api import AWSThing
from JciHitachi.model import STATUS_DICT


class TestStatusDict:
    device_types = AWSThing.supported_device_type.values()
    
    def test_sanity(self):    
        attribute_keys = { "controlable", "is_numeric", "legacy_name"}

        for device_type in self.device_types:
            for status_name, status_attributes in STATUS_DICT[device_type].items():
                # Test if attribute keys are in status attributes.
                assert len(attribute_keys - set(status_attributes)) == 0, \
                    f"Lack of attribute keys: {status_name} {set(status_attributes)}"
                # Test is_numeric and id2str mutual exclusiveness
                assert status_attributes["is_numeric"] ^ ("id2str" in status_attributes), \
                    f"is_numeric and id2str are mutual exclusive: {status_name}"
        