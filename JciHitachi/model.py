

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
    """Data model representing air conditioner status.

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
        'outdoor_temp': 33
    }

    def __init__(self, status, default=-1):
        super().__init__(status, default)
        
    @property
    def power(self):
        """Power.

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
        """Mode.

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
        """Air speed.

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
        """Target temperature.

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
        """Sleep timer.
        
        Returns
        -------
        int
            Sleep timer (hours).
        """

        v = self._status.get(self.idx['sleep_timer'], self._default)
        return v
    
    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable.

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
        """Vertical wind direction.

        Returns
        -------
        int
            Value between 0 to 15.
        """

        v = self._status.get(self.idx['vertical_wind_direction'], self._default)
        return v

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction.

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
        """Mold prevention.

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
        """Fast operation.

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
        """Energy saving.

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
        """Sound prompt.

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


class JciHitachiDH(JciHitachiStatus):
    """Data model representing dehumidifier status. Not implemented.

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
        'air_speed': 14,
        'air_quality_value': 35,
        'air_quality_level': 36,
        'pm25_value': 37,
        'odor_level': 40
    }

    def __init__(self, status, default=-1):
        super().__init__(status, default)
    
    @property
    def power(self):
        """Power.

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
        """Mode.

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
        """Target humidity.

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
    def wind_swingable(self):
        """Wind swingable.

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
    """Data model representing heat exchanger status. Not implemented.

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


class JciHitachiACSupport(JciHitachiStatus):
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
        'outdoor_temp': 33
    }

    def __init__(self, status, default=0):
        super().__init__(status, default)

    def _uni_v(self, v):
        return (((v >> 0x10 ) & 0xff) << 8) | (v >> 0x18)

    def _dual_v(self, v):
        low = (v >> 0x10) & 0xff
        high = (v >> 0x18) & 0xff
        return low, high
    
    def _functional_v(self, v):
        uni_v = self._uni_v(v)
        return ((uni_v >> i) & 0x1 for i in range(16))

    @property
    def brand(self):
        v = self._status.get(self.idx['brand'], self._default)
        return v

    @property
    def model(self):
        v = self._status.get(self.idx['model'], self._default)
        return v

    @property
    def power(self):
        """Power.

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
        """Mode.

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
        """Air speed.

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
        """Target temperature.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx['target_temp'], 0)
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

        v = self._status.get(self.idx['indoor_temp'], 0)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def sleep_timer(self):
        """Sleep timer.
        
        Returns
        -------
        (bool)
            (is_support, maximum).
        """

        v = self._status.get(self.idx['sleep_timer'], 0)
        support = self._uni_v(v)

        return (v != 0, support)
    
    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """
        
        v = self._status.get(self.idx['vertical_wind_swingable'], 0)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def vertical_wind_direction(self):
        """Vertical wind direction.

        Returns
        -------
        int
            Value between 0 to 15.
        """

        v = self._status.get(self.idx['vertical_wind_direction'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction.

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
        """Mold prevention.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['mold_prev'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def fast_op(self):
        """Fast operation.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['fast_op'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)
    
    @property
    def energy_save(self):
        """Energy saving.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx['energy_save'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def sound_prompt(self):
        """Sound prompt.

        Returns
        -------
        str
            One of ("unsupported", "enabled", "disabled", "unknown").
        """

        v = self._status.get(self.idx['sound_prompt'], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def outdoor_temp(self):
        """Outdoor temperature.
        
        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx['outdoor_temp'], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)
