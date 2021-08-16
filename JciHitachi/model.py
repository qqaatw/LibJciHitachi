

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
    """Data model representing air conditioner status.

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
    """Data model representing dehumidifier status. Not implemented.

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
        """Mode.

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
    """Data model representing heat exchanger status. Not implemented.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    """

    idx = {}

    def __init__(self, status):
        super().__init__(status)


class JciHitachiACSupport(JciHitachiStatus):
    """Data model representing supported air conditioner status.

    Parameters
    ----------
    status : dict
        Supported status retrieved from JciHitachiStatusInterpreter.decode_support().
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
