import base64

from . import utility as util


class JciHitachiCommand:
    """Abstract class for sending job command.

    Parameters
    ----------
    gateway_mac_address : str
        Gateway mac address.
    """

    def __init__(self, gateway_mac_address):
        self.job_info_base = bytearray.fromhex(
                              "d0d100003c6a9dffff03e0d4ffffffff \
                               00000100000000000000002000010000 \
                               000000000000000002000d278050f0d4 \
                               469dafd3605a6ebbdb130d278052f0d4 \
                               469dafd3605a6ebbdb13060006010000 \
                               0000")
        self.job_info_base[32:40] = bytearray.fromhex(hex(int(gateway_mac_address))[2:])
    
    def get_command(self, command, value):
        raise NotImplementedError
    
    def get_b64command(self, command, value):
        """A wrapper of get_command, generating base64 command.

        Parameters
        ----------
        command : str
            Status name.
        value : int
            Status value.

        Returns
        -------
        str
            Base64 command.
        """

        return base64.b64encode(self.get_command(command, value)).decode()


class JciHitachiCommandAC(JciHitachiCommand):
    """Sending job command to AC.

    Parameters
    ----------
    gateway_mac_address : str
        Gateway mac address.
    """
    
    def __init__(self, gateway_mac_address):
        super().__init__(gateway_mac_address)

    def get_command(self, command, value):
        """Get job command.

        Parameters
        ----------
        command : str
            Status name.
        value : int
            Status value.

        Returns
        -------
        bytearray
            Bytearray command.
        """

        job_info = self.job_info_base.copy()
        
        # Command (eg. target_temp)
        job_info[78] = 128 + JciHitachiAC.idx[command]

        # Value (eg. 27)
        job_info[80] = value

        # Checksum 
        # Original algorithm:
        # xor job_info 76~80
        # Since byte 76, 77, and 79 are constants,
        # here is the simplified algorithm:
        # command ^ value ^ 0x07 (flip last 3 bits) 
        job_info[81] = job_info[78] ^ job_info[80] ^ 0x07

        assert len(job_info) == 82, \
            "The length of job_info should be 82 bytes."

        return job_info


class JciHitachiStatusInterpreter:
    """Interpreting received status code.

    Parameters
    ----------
    code : str
        status code.
    """

    def __init__(self, code):
        self.base64_bytes = base64.standard_b64decode(code)
        self.status_number = self._decode_status_number()

    def _decode_status_number(self):
        if 6 < self.base64_bytes[0] and (self.base64_bytes[1], self.base64_bytes[2]) == (0, 8):
            return int((self.base64_bytes[0]-4)/3)
        else:
            return 0

    def _decode_single_status(self, max_func_number, while_counter):
        stat_idx = while_counter * 3 + 3

        if stat_idx + 3 <= self.base64_bytes[0] - 1:
            status_bytes = bytearray(4)
            status_bytes[0] = (self.base64_bytes[stat_idx] & 0x80) != 0
            status_bytes[1] = self.base64_bytes[stat_idx] & 0xffff7fff
            status_bytes[2:4] = self.base64_bytes[stat_idx + 1: stat_idx + 3]

            output = int.from_bytes(status_bytes, byteorder='little') 
            return output
        else:
            output = util.bin_concat(0xff, max_func_number)
            output = (output << 16) & 0xffff0000 | max_func_number
        return output

    def decode_status(self):
        """Decode all status of a peripheral.

        Returns
        -------
        dict
            Decoded status.
        """

        table = {}
        for i in range(self.status_number):
            ret = self._decode_single_status(self.status_number, i)
            idx = util.cast_bytes(ret >> 8, 1)
            table[idx] = ret >> 0x18 + (ret >> 0x10 * 0x100) 
        return table

class JciHitachiStatus:
    idx = {}

    def __init__(self, status) -> None:
        self._status = status

    @property
    def status(self):
        """All status.

        Returns
        -------
        dict
            All status.
        """

        return dict((key, getattr(self, key)) for key in self.idx)

class JciHitachiAC(JciHitachiStatus):
    """Data class representing air conditioner status.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    """

    idx = {
        'power': 0,
        'mode': 1,
        'air_speed': 2,
        'target_temp': 3,
        'indoor_temp': 4,
        'sleep_timer': 6,
        'vertical_wind_swingable': 14,
        'vertical_wind_direction': 15,
        'horizontal_wind_direction': 17, 
        'mold_prev': 23,
        'fast_op': 26,
        'energy_save': 27,
        'sound_prompt': 30,
        'outdoor_temp': 33
    }

    def __init__(self, status):
        super().__init__(status)
        
    @property
    def power(self):
        """Power.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['power'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"

    @property
    def mode(self):
        """Mode.

        Returns
        -------
        str
            One of ("unsupported", "cool", "dry", "fan", "auto", "heat", "unknown").
        """

        v = self._status.get(self.idx['mode'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "cool"
        elif v == 1:
            return "dry"
        elif v == 2:
            return "fan"
        elif v == 3:
            return "auto"
        elif v == 4:
            return "heat"
        else:
            return "unknown"

    @property
    def air_speed(self):
        """Air speed.

        Returns
        -------
        str
            One of ("unsupported", "auto", "silent", "low", "moderate", "high", "unknown").
        """

        v = self._status.get(self.idx['air_speed'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "auto"
        elif v == 1:
            return "silent"
        elif v == 2:
            return "low"
        elif v == 3:
            return "moderate"
        elif v == 4:
            return "high"
        else:
            return "unknown"

    @property
    def target_temp(self):
        """Target temperature.

        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx['target_temp'], -1)
        return v

    @property
    def indoor_temp(self):
        """Indoor temperature.

        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx['indoor_temp'], -1)
        return v
    
    @property
    def max_temp(self):
        """Maximum target temperature.

        Returns
        -------
        int
            Celsius temperature.
        """

        return 32
    
    @property
    def min_temp(self):
        """Minimum target temperature.
        
        Returns
        -------
        int
            Celsius temperature.
        """

        return 16

    @property
    def sleep_timer(self):
        """Sleep timer.
        
        Returns
        -------
        int
            Sleep timer (hours).
        """

        v = self._status.get(self.idx['sleep_timer'], -1)
        return v
    
    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """
        
        v = self._status.get(self.idx['vertical_wind_swingable'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"

    @property
    def vertical_wind_direction(self):
        """Vertical wind direction.

        Returns
        -------
        int
            Value between 0 to 15.
        """

        v = self._status.get(self.idx['vertical_wind_direction'], -1)
        return v

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction.

        Returns
        -------
        str
            One of ("unsupported", "auto", "leftmost", "middleleft", "central", "middleright", "rightmost", "unknown").
        """

        v = self._status.get(self.idx['horizontal_wind_direction'], -1)
        
        if v > 0: v = 6-v

        if v == -1:
            return "unsupported"
        elif v == 0:
            return "auto"
        elif v == 1:
            return "leftmost"
        elif v == 2:
            return "middleleft"
        elif v == 3:
            return "central"
        elif v == 4:
            return "middleright"
        elif v == 5:
            return "rightmost"
        else:
            return "unknown"

    @property
    def mold_prev(self):
        """Mold prevention.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['mold_prev'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"
    
    @property
    def fast_op(self):
        """Fast operation.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['fast_op'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"
    
    @property
    def energy_save(self):
        """Energy saving.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['energy_save'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"

    @property
    def sound_prompt(self):
        """Sound prompt.

        Returns
        -------
        str
            One of ("unsupported", "enabled", "disabled", "unknown").
        """

        v = self._status.get(self.idx['sound_prompt'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "enabled"
        elif v == 1:
            return "disabled"
        else:
            return "unknown"

    @property
    def outdoor_temp(self):
        """Outdoor temperature.
        
        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx['outdoor_temp'], -1)
        return v


class JciHitachiDH(JciHitachiStatus):
    """Data class representing dehumidifier status.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    """

    idx = {
        'power': 0,
        'mode': 1,
        'target_humidity': 3,
        'indoor_humidity': 7,
        'wind_swingable': 8,
        'water_full_warning': 10,
        'air_speed': 14,
        'air_quality_value': 35,
        'air_quality_level': 36,
        'pm25_value': 37,
        'odor_level': 40
    }

    def __init__(self, status):
        super().__init__(status)
    
    @property
    def power(self):
        """Power.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['power'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"
    
    @property
    def mode(self):
        """mode.

        Returns
        -------
        str
            One of (
                "unsupported", "auto", "custom", "continuous", "clothes_dry",
                "air_purify", "mold_prev", "low_humidity", "eco_comfort", "unknown"
            ).
        """

        v = self._status.get(self.idx['mode'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "auto"
        elif v == 1:
            return "custom"
        elif v == 2:
            return "continuous"
        elif v == 3:
            return "clothes_dry"
        elif v == 4:
            return "air_purify"
        elif v == 5:
            return "mold_prev"
        elif v == 8:
            return "low_humidity"
        elif v == 9:
            return "eco_comfort"
        else:
            return "unknown"

    @property
    def target_humidity(self):
        """Target humidity.

        Returns
        -------
        int
            Relative humidity.
        """

        v = self._status.get(self.idx['target_humidity'], -1)
        return v

    @property
    def indoor_humidity(self):
        """Indoor humidity.

        Returns
        -------
        int
            Relative humidity.
        """

        v = self._status.get(self.idx['indoor_humidity'], -1)
        return v
        
    @property
    def wind_swingable(self):
        """Wind swingable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['power'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"

    @property
    def water_full_warning(self):
        """Water full warning.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['water_full_warning'], -1)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"

    @property
    def air_speed(self):
        """Air speed. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        pass

    @property
    def air_quality_value(self):
        """Air quality value. Not implemented.

        Returns
        -------
        int
            Not implemented.
        """
        pass

    @property
    def air_quality_level(self):
        """Air quality level. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        pass
    
    @property
    def pm25_value(self):
        """PM2.5 value. Not implemented.

        Returns
        -------
        int
            Not implemented.
        """
        pass
    
    @property
    def odor_level(self):
        """Odor level. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        pass


class JciHitachiHE(JciHitachiStatus):
    """Data class representing heat exchanger status.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    """

    def __init__(self, status):
        super().__init__(status)