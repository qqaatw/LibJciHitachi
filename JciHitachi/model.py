import copy

class JciHitachiStatus:
    idx = {}

    def __init__(self, status, default) -> None:
        self._status = status
        self._default = default

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
    default : int, optional
        Default value when a status doesn't exist, by default -1.
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
        'outdoor_temp': 33,
        'power_kwh': 40,
    }

    def __init__(self, status, default=-1):
        super().__init__(status, default)
        
    @property
    def power(self):
        """Power. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['power'], self._default)
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
        """Mode. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "cool", "dry", "fan", "auto", "heat", "unknown").
        """

        v = self._status.get(self.idx['mode'], self._default)
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
        """Air speed. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "auto", "silent", "low", "moderate", "high", "unknown").
        """

        v = self._status.get(self.idx['air_speed'], self._default)
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
        """Target temperature. Controlable.

        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx['target_temp'], self._default)
        return v

    @property
    def indoor_temp(self):
        """Indoor temperature.

        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx['indoor_temp'], self._default)
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
        """Sleep timer. Controlable.
        
        Returns
        -------
        int
            Sleep timer (hours).
        """

        v = self._status.get(self.idx['sleep_timer'], self._default)
        return v
    
    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """
        
        v = self._status.get(self.idx['vertical_wind_swingable'], self._default)
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
        """Vertical wind direction. Controlable.

        Returns
        -------
        int
            Value between 0 to 15.
        """

        v = self._status.get(self.idx['vertical_wind_direction'], self._default)
        return v

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "auto", "leftmost", "middleleft", "central", "middleright", "rightmost", "unknown").
        """

        v = self._status.get(self.idx['horizontal_wind_direction'], self._default)
        
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
        """Mold prevention. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['mold_prev'], self._default)
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
        """Fast operation. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['fast_op'], self._default)
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
        """Energy saving. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['energy_save'], self._default)
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
        """Sound prompt. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "enabled", "disabled", "unknown").
        """

        v = self._status.get(self.idx['sound_prompt'], self._default)
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

        v = self._status.get(self.idx['outdoor_temp'], self._default)
        return v
    
    @property
    def power_kwh(self):
        """Accumulated Kwh in a day.

        Returns
        -------
        float
            Kwh.
        """

        v = self._status.get(self.idx['power_kwh'], self._default)
        if v == -1:
            return v
        return v / 10.0


class JciHitachiDH(JciHitachiStatus):
    """Data class representing dehumidifier status.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    default : int, optional
        Default value when a status doesn't exist, by default -1.
    """

    idx = {
        'power': 0,
        'mode': 1,
        'target_humidity': 3,
        'indoor_humidity': 7,
        'wind_swingable': 8,
        'water_full_warning': 10,
        'clean_filter_notify': 11,
        'air_purify_level': 13,
        'air_speed': 14,
        'side_vent': 15,
        'sound_control': 16,
        'error_code': 18,
        'mold_prev': 19,
        'power_kwh': 29,
        'air_quality_value': 35,
        'air_quality_level': 36,
        'pm25_value': 37,
        'display_brightness': 39,
        'odor_level': 40,
        'air_cleaning_filter': 41
    }

    def __init__(self, status, default=-1):
        super().__init__(status, default)
    
    @property
    def power(self):
        """Power. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['power'], self._default)
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
        """Mode. Controlable.

        Returns
        -------
        str
            One of (
            "unsupported", "auto", "custom", "continuous", "clothes_dry",
            "air_purify", "mold_prev", "low_humidity", "eco_comfort", "unknown"
            ).
        """

        v = self._status.get(self.idx['mode'], self._default)
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
        """Target humidity. Controlable.

        Returns
        -------
        int
            Relative humidity.
        """

        v = self._status.get(self.idx['target_humidity'], self._default)
        return v

    @property
    def indoor_humidity(self):
        """Indoor humidity.

        Returns
        -------
        int
            Relative humidity.
        """

        v = self._status.get(self.idx['indoor_humidity'], self._default)
        return v
    
    @property
    def max_humidity(self):
        """Maximum target humidity.

        Returns
        -------
        int
            Relative humidity.
        """

        return 70

    @property
    def min_humidity(self):
        """Minimum target humidity.

        Returns
        -------
        int
            Relative humidity.
        """

        return 40

    @property
    def wind_swingable(self):
        """Wind swingable. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['wind_swingable'], self._default)
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

        v = self._status.get(self.idx['water_full_warning'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"  # not activated
        elif v == 1:
            return "on"  # activated
        else:
            return "unknown"
    
    @property
    def clean_filter_notify(self):
        """Clean filter notify control. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['clean_filter_notify'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"

    @property
    def air_purify_level(self):
        """Air purify level. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        return "unsupported"

    @property
    def air_speed(self):
        """Air speed. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "auto", "silent", "low", "moderate", "high", "unknown").
        """

        v = self._status.get(self.idx['air_speed'], self._default)
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
    def side_vent(self):
        """Side vent.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['side_vent'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"

    @property
    def sound_control(self):
        """Sound control. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "silent", "button", "button+waterfull", "unknown").
        """

        v = self._status.get(self.idx['sound_control'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "silent"
        elif v == 1:
            return "button"
        elif v == 2:
            return "button+waterfull"
        else:
            return "unknown"

    @property
    def error_code(self):
        """Error code.

        Returns
        -------
        int
            Error code.
        """

        v = self._status.get(self.idx['error_code'], self._default)
        return v

    @property
    def mold_prev(self):
        """Mold prevention. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx['mold_prev'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"

    @property
    def power_kwh(self):
        """Accumulated Kwh in a day.

        Returns
        -------
        float
            Kwh.
        """

        v = self._status.get(self.idx['power_kwh'], self._default)
        if v == -1:
            return v
        return v / 10.0

    @property
    def air_quality_value(self):
        """Air quality value. Not implemented.

        Returns
        -------
        int
            Not implemented.
        """
        return self._default

    @property
    def air_quality_level(self):
        """Air quality level. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        return "unsupported"
    
    @property
    def pm25_value(self):
        """PM2.5 value.

        Returns
        -------
        int
            PM2.5 value.
        """

        v = self._status.get(self.idx['pm25_value'], self._default)
        return v
    
    @property
    def display_brightness(self):
        """Display brightness. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "bright", "dark", "off", "all_off" "unknown").
        """
        v = self._status.get(self.idx['display_brightness'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "bright"
        elif v == 1:
            return "dark"
        elif v == 2:
            return "off"
        elif v == 3:
            return "all_off"
        else:
            return "unknown"

    @property
    def odor_level(self):
        """Odor level.

        Returns
        -------
        str
            One of ("unsupported", "low", "middle", "high", "unknown").
        """
        v = self._status.get(self.idx['odor_level'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "low"
        elif v == 1:
            return "middle"
        elif v == 2:
            return "high"
        else:
            return "unknown"
    
    @property
    def air_cleaning_filter(self):
        """Air cleaning filter setting.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['air_cleaning_filter'], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"


class JciHitachiHE(JciHitachiStatus):
    """Data class representing heat exchanger status. Not implemented.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    default : int, optional
        Default value when a status doesn't exist, by default -1.
    """

    idx = {}

    def __init__(self, status, default=-1):
        super().__init__(status, default)


class JciHitachiStatusSupport(JciHitachiStatus):
    supported_type = {}

    def __init__(self, status, default=0):
        super().__init__(status, default)

    @property
    def brand(self):
        """Device brand.

        Returns
        -------
        str
            Device brand.
        """

        v = self._status.get(self.idx['brand'], self._default)
        return v

    @property
    def model(self):
        """Device model.

        Returns
        -------
        str
            Device model.
        """

        v = self._status.get(self.idx['model'], self._default)
        return v

    def _uni_v(self, v):
        return (((v >> 0x10) & 0xff) << 8) | (v >> 0x18)

    def _dual_v(self, v):
        low = (v >> 0x10) & 0xff
        high = (v >> 0x18) & 0xff
        return low, high

    def _functional_v(self, v):
        uni_v = self._uni_v(v)
        return ((uni_v >> i) & 0x1 for i in range(16))
    
    def limit(self, status_name, status_value):
        """Limit status_value within an acceptable range.

        Parameters
        ----------
        status_name : str
            Status name, which has to be in idx dict. E.g. JciHitachiAC.idx
        status_value : int
            Status value.

        Returns
        -------
        int or None
            If the status_value can be limited with an acceptable raneg, return int. 
            Otherwise, if the status_value is invalid, return None.
        """

        is_support, *v = getattr(self, status_name)
        if not is_support:
            return None
        
        supported_type = self.supported_type[status_name]
        if supported_type == "uni":
            return min(status_value, v[0])
        elif supported_type == "dual":
            return min(v[1], max(status_value, v[0]))
        elif supported_type == "functional":
            if v[status_value]: return status_value
        return None


class JciHitachiACSupport(JciHitachiStatusSupport):
    """Data model representing supported air conditioner status.

    Parameters
    ----------
    status : dict
        Supported status retrieved from JciHitachiStatusInterpreter.decode_support().
    default : int, optional
        Default value when a status doesn't exist, by default 0.
    """

    idx = {
        'brand': "brand",
        'model': "model",
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
        'outdoor_temp': 33,
        'power_kwh': 40,
    }

    supported_type = {
        'brand': 'str',
        'model': 'str',
        'power': 'functional',
        'mode': 'functional',
        'air_speed': 'functional',
        'target_temp': 'dual',
        'indoor_temp': 'dual',
        'sleep_timer': 'uni',
        'vertical_wind_swingable': 'functional',
        'vertical_wind_direction': 'functional',
        'horizontal_wind_direction': 'functional',
        'mold_prev': 'functional',
        'fast_op': 'functional',
        'energy_save': 'functional',
        'sound_prompt': 'functional',
        'outdoor_temp': 'dual',
        'power_kwh': 'uni',
    }

    def __init__(self, status, default=0):
        super().__init__(status, default)

    @property
    def power(self):
        """Power. Controlable.

        Returns
        -------
        (bool, int, int)
            (is_support, off, on).
        """

        v = self._status.get(self.idx['power'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def mode(self):
        """Mode. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, (cool, dry, fan, auto, heat, 0...).
        """

        v = self._status.get(self.idx['mode'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def air_speed(self):
        """Air speed. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "silent", "low", "moderate", "high", 0...).
        """

        v = self._status.get(self.idx['air_speed'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def target_temp(self):
        """Target temperature. Controlable.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx['target_temp'], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def indoor_temp(self):
        """Indoor temperature.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx['indoor_temp'], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def sleep_timer(self):
        """Sleep timer. Controlable.
        
        Returns
        -------
        (bool, int)
            (is_support, maximum).
        """

        v = self._status.get(self.idx['sleep_timer'], self._default)
        support = self._uni_v(v)

        return (v != 0, support)
    
    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """
        
        v = self._status.get(self.idx['vertical_wind_swingable'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def vertical_wind_direction(self):
        """Vertical wind direction. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "level1", "level2", "level3", "level4", "level5", "level6", "level7", 0...).
        """

        v = self._status.get(self.idx['vertical_wind_direction'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "leftmost", "middleleft", "central", "middleright", "rightmost", 0...).
        """

        v = self._status.get(self.idx['horizontal_wind_direction'], self._default)
        if v > 0: v = 6-v

        supports = self._functional_v(v)
        return (v != 0, *supports)

    @property
    def mold_prev(self):
        """Mold prevention. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx['mold_prev'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def fast_op(self):
        """Fast operation. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("disabled", "enabled", 0...).
        """

        v = self._status.get(self.idx['fast_op'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def energy_save(self):
        """Energy saving. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx['energy_save'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def sound_prompt(self):
        """Sound prompt. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx['sound_prompt'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def outdoor_temp(self):
        """Outdoor temperature.
        
        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx['outdoor_temp'], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)
    
    @property
    def power_kwh(self):
        """Accumulated Kwh in a day.

        Returns
        -------
        (bool, int)
            (is_support, maximum).
        """

        v = self._status.get(self.idx['power_kwh'], self._default)
        supports = self._uni_v(v)

        return (v != 0, supports)


class JciHitachiDHSupport(JciHitachiStatusSupport):
    """Data model representing supported dehumidifier status.

    Parameters
    ----------
    status : dict
        Supported status retrieved from JciHitachiStatusInterpreter.decode_support().
    default : int, optional
        Default value when a status doesn't exist, by default 0.
    """

    idx = {
        'brand': "brand",
        'model': "model",
        'power': 0,
        'mode': 1,
        'target_humidity': 3,
        'indoor_humidity': 7,
        'wind_swingable': 8,
        'water_full_warning': 10,
        'clean_filter_notify': 11,
        'air_purify_level': 13,
        'air_speed': 14,
        'side_vent': 15,
        'sound_control': 16,
        'error_code': 18,
        'mold_prev': 19,
        'power_kwh': 29,
        'air_quality_value': 35,
        'air_quality_level': 36,
        'pm25_value': 37,
        'display_brightness': 39,
        'odor_level': 40,
        'air_cleaning_filter': 41
    }

    supported_type = {
        'brand': 'str',
        'model': 'str',
        'power': 'functional',
        'mode': 'functional',
        'target_humidity': 'dual',
        'indoor_humidity': 'dual',
        'wind_swingable': 'functional',
        'water_full_warning': 'functional',
        'clean_filter_notify': 'functional',
        'air_purify_level': 'functional', # not implemented
        'air_speed': 'functional',
        'side_vent': 'functional',
        'sound_control': 'functional',
        'error_code': 'uni',
        'mold_prev': 'functional',
        'power_kwh': 'uni',
        'air_quality_value': 'uni',
        'air_quality_level': 'functional',
        'pm25_value': 'uni',
        'display_brightness': 'functional',
        'odor_level': 'functional',
        'air_cleaning_filter': 'functional'
    }

    def __init__(self, status, default=0):
        super().__init__(status, default)
    
    @property
    def power(self):
        """Power. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            (is_support, off, on).
        """

        v = self._status.get(self.idx['power'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def mode(self):
        """Mode. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, (auto, custom, continuous, clothes_dry, air_purify, mold_prev, air_supply, human_comfort, low_humidity, eco_comfort, 0...). 
        """

        v = self._status.get(self.idx['mode'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def target_humidity(self):
        """Target humidity. Controlable.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx['target_humidity'], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def indoor_humidity(self):
        """Indoor humidity.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx['indoor_humidity'], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def wind_swingable(self):
        """Wind swingable. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("off", "on", 0...).
        """
        

        v = self._status.get(self.idx['wind_swingable'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def water_full_warning(self):
        """Water full warning.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("off", "on", 0...).
        """

        v = self._status.get(self.idx['water_full_warning'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def clean_filter_notify(self):
        """Clean filter notify control. Controlable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['clean_filter_notify'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def air_purify_level(self):
        """Air purify level. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        
        return "unsupported"

    @property
    def air_speed(self):
        """Air speed. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "silent", "low", "moderate", "high", 0...).
        """

        v = self._status.get(self.idx['air_speed'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def side_vent(self):
        """Side vent.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("off", "on", 0...).
        """

        v = self._status.get(self.idx['side_vent'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def sound_control(self):
        """Sound control. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("silent", "button", "button+waterfull", 0...).    
        """

        v = self._status.get(self.idx['sound_control'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def error_code(self):
        """Error code.

        Returns
        -------
        (bool,)
            (is_support,).
        """

        v = self._status.get(self.idx['error_code'], self._default)

        return (v != 0,)

    @property
    def mold_prev(self):
        """Mold prevention. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("silent", "off", "on",, 0...).  
        """

        v = self._status.get(self.idx['mold_prev'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def power_kwh(self):
        """Accumulated Kwh in a day.

        Returns
        -------
        (bool, int)
            (is_support, maximum).
        """

        v = self._status.get(self.idx['power_kwh'], self._default)
        supports = self._uni_v(v)

        return (v != 0, supports)

    @property
    def air_quality_value(self):
        """Air quality value. Not implemented.

        Returns
        -------
        int
            Not implemented.
        """
        return self._default

    @property
    def air_quality_level(self):
        """Air quality level. Not implemented.

        Returns
        -------
        str
            Not implemented.
        """
        return "unsupported"
    
    @property
    def pm25_value(self):
        """PM2.5 value.

        Returns
        -------
        (bool, int)
            (is_support, maximum).
        """

        v = self._status.get(self.idx['pm25_value'], self._default)
        supports = self._uni_v(v)

        return (v != 0, supports)
    
    @property
    def display_brightness(self):
        """Display brightness. Controlable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("bright", "dark", "off", 0...).  
        """

        v = self._status.get(self.idx['display_brightness'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def odor_level(self):
        """Odor level.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("low", "middle", "high", 0...).  
        """

        v = self._status.get(self.idx['odor_level'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def air_cleaning_filter(self):
        """Air cleaning filter setting.

        Returns
        -------
        (bool, Tuple[int]) 
            is_support, ("enabled", "disabled", 0...). status's reversed order.
        """

        v = self._status.get(self.idx['air_cleaning_filter'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)


class JciHitachiHESupport(JciHitachiStatusSupport):
    """Data model representing supported heat exchanger status. Not implemented.

    Parameters
    ----------
    status : dict
        Supported status retrieved from JciHitachiStatusInterpreter.decode_support().
    default : int, optional
        Default value when a status doesn't exist, by default 0.
    """

    idx = {}

    def __init__(self, status, default=0):
        super().__init__(status, default)



class JciHitachiAWSStatus:
    compability_mapping = {
        "AC": {
            'DeviceType': None,
            'Switch': 'power',
            'Mode': 'mode',
            'FanSpeed': 'air_speed',
            'TemperatureSetting': 'target_temp',
            'IndoorTemperature': 'indoor_temp',
            'OutdoorTemperature': 'outdoor_temp',
            'SleepModeRemainingTime': 'sleep_timer',
            'VerticalWindDirectionSwitch': 'vertical_wind_swingable', 
            'VerticalWindDirectionSetting': 'vertical_wind_direction',
            'HorizontalWindDirectionSetting': 'horizontal_wind_direction',
            'MildewProof': 'mold_prev',
            'QuickMode': 'fast_op',
            'PowerSaving': 'energy_save',
            'ControlTone': 'sound_prompt',
            'PowerConsumption': 'power_kwh',
            'TaiseiaError': None,
            'FilterElapsedHour': None,
            'CleanSwitch': None,
            'CleanNotification': None,
            'CleanStatus': None,
            'Error': None,
        },
        "DH": {
            'DeviceType': None,
            'Switch': 'power',
            'Mode': 'mode',
            'FanSpeed': 'air_speed',
            'MildewProof': 'mold_prev',
            'ControlTone': 'sound_control',
            'SaaControlTone': None,
            'PowerConsumption': 'power_kwh',
            'Ion': None,
            'HumiditySetting': 'target_humidity',
            'AutoWindDirection': 'wind_swingable',
            'KeypadLock': None,
            'DisplayBrightness': 'display_brightness',
            'FilterControl': 'air_cleaning_filter',
            'PM25': 'pm25_value',
            'IndoorHumidity': 'indoor_humidity',
            'SideAirOutlet': 'side_vent',
            'Defrost': None,
            'SmellIndex': 'odor_level',
            'CleanFilterNotification': 'clean_filter_notify',
            'TankFullNotification': 'water_full_warning',
            'TaiseiaError': None,
            'Error': 'error_code',
        }
    }
    device_type_mapping = {
        1: "AC",
        2: "DH",
        3: "HE",
        4: "PM25_PANEL",
    }

    def __init__(self, status: dict) -> None:
        self._status: dict = self._preprocess(status)

    def __getattr__(self, item):
        print(item)
        return self._status[item]
    
    def __repr__(self) -> str:
        return str(self._status)

    def _preprocess(self, status):
        # device type
        if status.get("DeviceType"):
            status["DeviceType"] = self.device_type_mapping[status["DeviceType"]]
        
        if not status.get("OutdoorTemperature"):
            status["OutdoorTemperature"] = 0
        
        return status

    @property
    def status(self):
        """All status.

        Returns
        -------
        dict
            All status.
        """

        return self._status
    
    @property
    def legacy_status_class(self):
        """All legacy status used by the old API.

        Returns
        -------
        JciHitachiStatus
            status.
        """

        class mock_idx(dict):
            def __getitem__(self, key):
                return key

        mapped_status = {self.compability_mapping[self._status["DeviceType"]].get(key): value for key, value in self._status.items()}

        if self._status["DeviceType"] == "AC":
            if None in mapped_status:
                del mapped_status[None]
            ac = JciHitachiAC(mapped_status)
            ac.idx = mock_idx(ac.idx)
            return ac
        elif self._status["DeviceType"] == "DH":
            if None in mapped_status:
                del mapped_status[None]
            dh = JciHitachiDH(mapped_status)
            dh.idx = mock_idx(dh.idx)
            return dh
        return None

    @staticmethod
    def convert_old_to_new(device_type, old_status_name):
        for key, value in __class__.compability_mapping[device_type].items():
            if value == old_status_name:
                return key
        return None

class JciHitachiAWSStatusSupport:
    extended_mapping = {
        "FirmwareId": None,
        "Model": "model",
        "Brand": "brand",
        "FindMe": None,
    }

    compability_mapping = copy.deepcopy(JciHitachiAWSStatus.compability_mapping).update(extended_mapping)
    device_type_mapping = JciHitachiAWSStatus.device_type_mapping

    def __init__(self, status: dict) -> None:
        self._status: dict = self._preprocess(status)

    def __getattr__(self, item):
        return self._status[item]
    
    def __repr__(self) -> str:
        return str(self._status)

    def _preprocess(self, status):
        # device type
        if status.get("DeviceType"):
            status["DeviceType"] = self.device_type_mapping[status["DeviceType"]]
        
        if not status.get("OutdoorTemperature"):
            status["OutdoorTemperature"] = 0
        
        status["Brand"] = "HITACHI"
        
        return status

    @property
    def status(self):
        """All status.

        Returns
        -------
        dict
            All status.
        """

        return self._status