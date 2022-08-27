import os

# For integration tests
TEST_EMAIL =  os.environ["TEST_EMAIL"] if "TEST_EMAIL" in os.environ else None
TEST_PASSWORD = os.environ['TEST_PASSWORD'] if "TEST_PASSWORD" in os.environ else None
TEST_DEVICE_AC = os.environ['TEST_DEVICE_AC'] if "TEST_DEVICE_AC" in os.environ else None
TEST_DEVICE_DH = os.environ['TEST_DEVICE_DH'] if "TEST_DEVICE_DH" in os.environ else None

MOCK_GATEWAY_MAC = '10416149025290813292'

# AC
MOCK_DEVICE_AC = "Welcome AC"
MOCK_COMMAND_AC = 'sound_prompt'
MOCK_CODE_AC = "QwAIAAAAAQAAAgABAwAaBAAaBgAACwAADAAAFwAAGgAAGwAAHQAAHgAAIQAYKAAAKQAALwOAMAMgOQAAOgABOwAA5A=="
MOCK_SUPPORT_CODE_AC = "WQAABAADAAFISVRBQ0hJAFJBRC05ME5GAIAAA4EAH4IAH4MQIAQAKIYFoIsFoIwFoJcAA5oAA5sAA50AP54AAyHpKKj//ykAVa9SWLADILkAAzoAAzsAB14="
# DH
MOCK_DEVICE_DH = "Welcome DH"
MOCK_COMMAND_DH = 'sound_control'
MOCK_CODE_DH = "RgAIAAABAQABAgAAAwBGBwBGCAABCgAACwAADQAADgABDwAAEAACEQAAEgAAEwAAFgAAGAAAHQAEJQAaJwAAKAABKQABQQ=="
MOCK_SUPPORT_CODE_DH = "XAAABAADAARISVRBQ0hJAFJELTM2MEhIAIAAA4EDOoIADIMoRgceWogAAwoAA4sAA40AA44AHg8AA5AABREAAxIACpMAA5YAA5gAA53//yXoA6cADygAB6kAA3s="
# HE
MOCK_DEVICE_HE = "Welcome HE"