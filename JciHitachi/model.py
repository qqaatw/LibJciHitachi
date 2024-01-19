from functools import lru_cache


class JciHitachiStatus:  # pragma: no cover
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


class JciHitachiAC(JciHitachiStatus):  # pragma: no cover
    """Data class representing air conditioner status.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    default : int, optional
        Default value when a status doesn't exist, by default -1.
    """

    idx = {
        "power": 0,
        "mode": 1,
        "air_speed": 2,
        "target_temp": 3,
        "indoor_temp": 4,
        "sleep_timer": 6,
        "vertical_wind_swingable": 14,
        "vertical_wind_direction": 15,
        "horizontal_wind_direction": 17,
        "mold_prev": 23,
        "fast_op": 26,
        "energy_save": 27,
        "sound_prompt": 30,
        "outdoor_temp": 33,
        "power_kwh": 40,
        "freeze_clean": 57,
    }

    def __init__(self, status, default=-1):
        super().__init__(status, default)

    @property
    def power(self):
        """Power. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx["power"], self._default)
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
        """Mode. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "cool", "dry", "fan", "auto", "heat", "unknown").
        """

        v = self._status.get(self.idx["mode"], self._default)
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
        """Air speed. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "auto", "silent", "low", "moderate", "high", "unknown").
        """

        v = self._status.get(self.idx["air_speed"], self._default)
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
        """Target temperature. Controllable.

        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx["target_temp"], self._default)
        return v

    @property
    def indoor_temp(self):
        """Indoor temperature.

        Returns
        -------
        int
            Celsius temperature.
        """

        v = self._status.get(self.idx["indoor_temp"], self._default)
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
        """Sleep timer. Controllable.

        Returns
        -------
        int
            Sleep timer (hours).
        """

        v = self._status.get(self.idx["sleep_timer"], self._default)
        return v

    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx["vertical_wind_swingable"], self._default)
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
        """Vertical wind direction. Controllable.

        Returns
        -------
        int
            Value between 0 to 15.
        """

        v = self._status.get(self.idx["vertical_wind_direction"], self._default)
        return v

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "auto", "leftmost", "middleleft", "central", "middleright", "rightmost", "unknown").
        """

        v = self._status.get(self.idx["horizontal_wind_direction"], self._default)

        if v > 0:
            v = 6 - v

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
        """Mold prevention. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx["mold_prev"], self._default)
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
        """Fast operation. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx["fast_op"], self._default)
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
        """Energy saving. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx["energy_save"], self._default)
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
        """Sound prompt. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "enabled", "disabled", "unknown").
        """

        v = self._status.get(self.idx["sound_prompt"], self._default)
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

        v = self._status.get(self.idx["outdoor_temp"], self._default)
        return v

    @property
    def power_kwh(self):
        """Accumulated Kwh in a day.

        Returns
        -------
        float
            Kwh.
        """

        v = self._status.get(self.idx["power_kwh"], self._default)
        if v == -1:
            return v
        return v / 10.0

    @property
    def freeze_clean(self):
        """Freeze clean. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx["freeze_clean"], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "off"
        elif v == 1:
            return "on"
        else:
            return "unknown"


class JciHitachiDH(JciHitachiStatus):  # pragma: no cover
    """Data class representing dehumidifier status.

    Parameters
    ----------
    status : dict
        Status retrieved from JciHitachiStatusInterpreter.decode_status().
    default : int, optional
        Default value when a status doesn't exist, by default -1.
    """

    idx = {
        "power": 0,
        "mode": 1,
        "target_humidity": 3,
        "indoor_humidity": 7,
        "wind_swingable": 8,
        "water_full_warning": 10,
        "clean_filter_notify": 11,
        "air_purify_level": 13,
        "air_speed": 14,
        "side_vent": 15,
        "sound_control": 16,
        "error_code": 18,
        "mold_prev": 19,
        "power_kwh": 29,
        "air_quality_value": 35,
        "air_quality_level": 36,
        "pm25_value": 37,
        "display_brightness": 39,
        "odor_level": 40,
        "air_cleaning_filter": 41,
    }

    def __init__(self, status, default=-1):
        super().__init__(status, default)

    @property
    def power(self):
        """Power. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx["power"], self._default)
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
        """Mode. Controllable.

        Returns
        -------
        str
            One of (
            "unsupported", "auto", "custom", "continuous", "clothes_dry",
            "air_purify", "mold_prev", "low_humidity", "eco_comfort", "unknown"
            ).
        """

        v = self._status.get(self.idx["mode"], self._default)
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
        """Target humidity. Controllable.

        Returns
        -------
        int
            Relative humidity.
        """

        v = self._status.get(self.idx["target_humidity"], self._default)
        return v

    @property
    def indoor_humidity(self):
        """Indoor humidity.

        Returns
        -------
        int
            Relative humidity.
        """

        v = self._status.get(self.idx["indoor_humidity"], self._default)
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
        """Wind swingable. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx["wind_swingable"], self._default)
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

        v = self._status.get(self.idx["water_full_warning"], self._default)
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
        """Clean filter notify control. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx["clean_filter_notify"], self._default)
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
        """Air speed. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "auto", "silent", "low", "moderate", "high", "unknown").
        """

        v = self._status.get(self.idx["air_speed"], self._default)
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

        v = self._status.get(self.idx["side_vent"], self._default)
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
        """Sound control. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "silent", "button", "button+waterfull", "unknown").
        """

        v = self._status.get(self.idx["sound_control"], self._default)
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

        v = self._status.get(self.idx["error_code"], self._default)
        return v

    @property
    def mold_prev(self):
        """Mold prevention. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "off", "on", "unknown").
        """

        v = self._status.get(self.idx["mold_prev"], self._default)
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

        v = self._status.get(self.idx["power_kwh"], self._default)
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

        v = self._status.get(self.idx["pm25_value"], self._default)
        return v

    @property
    def display_brightness(self):
        """Display brightness. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "bright", "dark", "off", "all_off" "unknown").
        """
        v = self._status.get(self.idx["display_brightness"], self._default)
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
        v = self._status.get(self.idx["odor_level"], self._default)
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

        v = self._status.get(self.idx["air_cleaning_filter"], self._default)
        if v == -1:
            return "unsupported"
        elif v == 0:
            return "disabled"
        elif v == 1:
            return "enabled"
        else:
            return "unknown"


class JciHitachiHE(JciHitachiStatus):  # pragma: no cover
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


class JciHitachiStatusSupport(JciHitachiStatus):  # pragma: no cover
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

        v = self._status.get(self.idx["brand"], self._default)
        return v

    @property
    def model(self):
        """Device model.

        Returns
        -------
        str
            Device model.
        """

        v = self._status.get(self.idx["model"], self._default)
        return v

    def _uni_v(self, v):
        return (((v >> 0x10) & 0xFF) << 8) | (v >> 0x18)

    def _dual_v(self, v):
        low = (v >> 0x10) & 0xFF
        high = (v >> 0x18) & 0xFF
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
            if v[status_value]:
                return status_value
        return None


class JciHitachiACSupport(JciHitachiStatusSupport):  # pragma: no cover
    """Data model representing supported air conditioner status.

    Parameters
    ----------
    status : dict
        Supported status retrieved from JciHitachiStatusInterpreter.decode_support().
    default : int, optional
        Default value when a status doesn't exist, by default 0.
    """

    idx = {
        "brand": "brand",
        "model": "model",
        "power": 0,
        "mode": 1,
        "air_speed": 2,
        "target_temp": 3,
        "indoor_temp": 4,
        "sleep_timer": 6,
        "vertical_wind_swingable": 14,
        "vertical_wind_direction": 15,
        "horizontal_wind_direction": 17,
        "mold_prev": 23,
        "fast_op": 26,
        "energy_save": 27,
        "sound_prompt": 30,
        "outdoor_temp": 33,
        "power_kwh": 40,
    }

    supported_type = {
        "brand": "str",
        "model": "str",
        "power": "functional",
        "mode": "functional",
        "air_speed": "functional",
        "target_temp": "dual",
        "indoor_temp": "dual",
        "sleep_timer": "uni",
        "vertical_wind_swingable": "functional",
        "vertical_wind_direction": "functional",
        "horizontal_wind_direction": "functional",
        "mold_prev": "functional",
        "fast_op": "functional",
        "energy_save": "functional",
        "sound_prompt": "functional",
        "outdoor_temp": "dual",
        "power_kwh": "uni",
    }

    def __init__(self, status, default=0):
        super().__init__(status, default)

    @property
    def power(self):
        """Power. Controllable.

        Returns
        -------
        (bool, int, int)
            (is_support, off, on).
        """

        v = self._status.get(self.idx["power"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def mode(self):
        """Mode. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, (cool, dry, fan, auto, heat, 0...).
        """

        v = self._status.get(self.idx["mode"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def air_speed(self):
        """Air speed. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "silent", "low", "moderate", "high", 0...).
        """

        v = self._status.get(self.idx["air_speed"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def target_temp(self):
        """Target temperature. Controllable.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx["target_temp"], self._default)
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

        v = self._status.get(self.idx["indoor_temp"], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def sleep_timer(self):
        """Sleep timer. Controllable.

        Returns
        -------
        (bool, int)
            (is_support, maximum).
        """

        v = self._status.get(self.idx["sleep_timer"], self._default)
        support = self._uni_v(v)

        return (v != 0, support)

    @property
    def vertical_wind_swingable(self):
        """Vertical wind swingable. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx["vertical_wind_swingable"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def vertical_wind_direction(self):
        """Vertical wind direction. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "level1", "level2", "level3", "level4", "level5", "level6", "level7", 0...).
        """

        v = self._status.get(self.idx["vertical_wind_direction"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def horizontal_wind_direction(self):
        """Horizontal wind direction. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "leftmost", "middleleft", "central", "middleright", "rightmost", 0...).
        """

        v = self._status.get(self.idx["horizontal_wind_direction"], self._default)
        if v > 0:
            v = 6 - v

        supports = self._functional_v(v)
        return (v != 0, *supports)

    @property
    def mold_prev(self):
        """Mold prevention. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx["mold_prev"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def fast_op(self):
        """Fast operation. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("disabled", "enabled", 0...).
        """

        v = self._status.get(self.idx["fast_op"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def energy_save(self):
        """Energy saving. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx["energy_save"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def sound_prompt(self):
        """Sound prompt. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("enabled", "disabled", 0...).
        """

        v = self._status.get(self.idx["sound_prompt"], self._default)
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

        v = self._status.get(self.idx["outdoor_temp"], self._default)
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

        v = self._status.get(self.idx["power_kwh"], self._default)
        supports = self._uni_v(v)

        return (v != 0, supports)


class JciHitachiDHSupport(JciHitachiStatusSupport):  # pragma: no cover
    """Data model representing supported dehumidifier status.

    Parameters
    ----------
    status : dict
        Supported status retrieved from JciHitachiStatusInterpreter.decode_support().
    default : int, optional
        Default value when a status doesn't exist, by default 0.
    """

    idx = {
        "brand": "brand",
        "model": "model",
        "power": 0,
        "mode": 1,
        "target_humidity": 3,
        "indoor_humidity": 7,
        "wind_swingable": 8,
        "water_full_warning": 10,
        "clean_filter_notify": 11,
        "air_purify_level": 13,
        "air_speed": 14,
        "side_vent": 15,
        "sound_control": 16,
        "error_code": 18,
        "mold_prev": 19,
        "power_kwh": 29,
        "air_quality_value": 35,
        "air_quality_level": 36,
        "pm25_value": 37,
        "display_brightness": 39,
        "odor_level": 40,
        "air_cleaning_filter": 41,
    }

    supported_type = {
        "brand": "str",
        "model": "str",
        "power": "functional",
        "mode": "functional",
        "target_humidity": "dual",
        "indoor_humidity": "dual",
        "wind_swingable": "functional",
        "water_full_warning": "functional",
        "clean_filter_notify": "functional",
        "air_purify_level": "functional",  # not implemented
        "air_speed": "functional",
        "side_vent": "functional",
        "sound_control": "functional",
        "error_code": "uni",
        "mold_prev": "functional",
        "power_kwh": "uni",
        "air_quality_value": "uni",
        "air_quality_level": "functional",
        "pm25_value": "uni",
        "display_brightness": "functional",
        "odor_level": "functional",
        "air_cleaning_filter": "functional",
    }

    def __init__(self, status, default=0):
        super().__init__(status, default)

    @property
    def power(self):
        """Power. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            (is_support, off, on).
        """

        v = self._status.get(self.idx["power"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def mode(self):
        """Mode. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, (auto, custom, continuous, clothes_dry, air_purify, mold_prev, air_supply, human_comfort, low_humidity, eco_comfort, 0...).
        """

        v = self._status.get(self.idx["mode"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def target_humidity(self):
        """Target humidity. Controllable.

        Returns
        -------
        (bool, int, int)
            (is_support, minimum, maximum)
        """

        v = self._status.get(self.idx["target_humidity"], self._default)
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

        v = self._status.get(self.idx["indoor_humidity"], self._default)
        supports = self._dual_v(v)

        return (v != 0, *supports)

    @property
    def wind_swingable(self):
        """Wind swingable. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("off", "on", 0...).
        """

        v = self._status.get(self.idx["wind_swingable"], self._default)
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

        v = self._status.get(self.idx["water_full_warning"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def clean_filter_notify(self):
        """Clean filter notify control. Controllable.

        Returns
        -------
        str
            One of ("unsupported", "disabled", "enabled", "unknown").
        """

        v = self._status.get(self.idx["clean_filter_notify"], self._default)
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
        """Air speed. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("auto", "silent", "low", "moderate", "high", 0...).
        """

        v = self._status.get(self.idx["air_speed"], self._default)
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

        v = self._status.get(self.idx["side_vent"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)

    @property
    def sound_control(self):
        """Sound control. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("silent", "button", "button+waterfull", 0...).
        """

        v = self._status.get(self.idx["sound_control"], self._default)
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

        v = self._status.get(self.idx["error_code"], self._default)

        return (v != 0,)

    @property
    def mold_prev(self):
        """Mold prevention. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("silent", "off", "on",, 0...).
        """

        v = self._status.get(self.idx["mold_prev"], self._default)
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

        v = self._status.get(self.idx["power_kwh"], self._default)
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

        v = self._status.get(self.idx["pm25_value"], self._default)
        supports = self._uni_v(v)

        return (v != 0, supports)

    @property
    def display_brightness(self):
        """Display brightness. Controllable.

        Returns
        -------
        (bool, Tuple[int])
            is_support, ("bright", "dark", "off", 0...).
        """

        v = self._status.get(self.idx["display_brightness"], self._default)
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

        v = self._status.get(self.idx["odor_level"], self._default)
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

        v = self._status.get(self.idx["air_cleaning_filter"], self._default)
        supports = self._functional_v(v)

        return (v != 0, *supports)


class JciHitachiHESupport(JciHitachiStatusSupport):  # pragma: no cover
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


STATUS_DICT = {
    "AC": {
        "DeviceType": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": "DeviceType",
            "id2str": {
                1: "AC",
                2: "DH",
                3: "HE",
                4: "PM25_PANEL",
            },
        },
        "Switch": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "power",
            "id2str": {
                0: "off",
                1: "on",
            },
        },
        "Mode": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "mode",
            "id2str": {
                0: "cool",
                1: "dry",
                2: "fan",
                3: "auto",
                4: "heat",
            },
        },
        "FanSpeed": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "air_speed",
            "id2str": {
                0: "auto",
                1: "silent",
                2: "low",
                3: "moderate",
                4: "high",
                5: "rapid",
                6: "express",
            },
        },
        "TemperatureSetting": {
            "controllable": True,
            "is_numeric": True,
            "legacy_name": "target_temp",
        },
        "IndoorTemperature": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "indoor_temp",
        },
        "SleepModeRemainingTime": {
            "controllable": True,
            "is_numeric": True,
            "legacy_name": "sleep_timer",
        },
        "VerticalWindDirectionSwitch": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "vertical_wind_swingable",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "VerticalWindDirectionSetting": {
            "controllable": True,
            "is_numeric": True,
            "legacy_name": "vertical_wind_direction",
        },
        "HorizontalWindDirectionSetting": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "horizontal_wind_direction",
            "id2str": {
                0: "auto",
                1: "leftmost",
                2: "middleleft",
                3: "central",
                4: "middleright",
                5: "rightmost",
            },
        },
        "MildewProof": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "mold_prev",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "QuickMode": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "fast_op",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "PowerSaving": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "energy_save",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "ControlTone": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "sound_prompt",
            "id2str": {
                0: "enabled",
                1: "disabled",
            },
        },
        "PowerConsumption": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "power_kwh",
        },
        "TaiseiaError": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "FilterElapsedHour": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "CleanSwitch": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "freeze_clean",
            "id2str": {
                0: "off",
                1: "on",
            },
        },
        "CleanNotification": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "CleanStatus": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "Error": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "max_temp": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "max_temp",
        },
        "min_temp": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "min_temp",
        },
        "Panel": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "bright",
                1: "dark",
                2: "off",
                3: "all_off",
            },
        },
    },
    "DH": {
        "DeviceType": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": "DeviceType",
            "id2str": {
                1: "AC",
                2: "DH",
                3: "HE",
                4: "PM25_PANEL",
            },
        },
        "Switch": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "power",
            "id2str": {
                0: "off",
                1: "on",
            },
        },
        "Mode": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "mode",
            "id2str": {
                0: "auto",
                1: "custom",
                2: "continuous",
                3: "clothes_dry",
                4: "air_purify",
                5: "mold_prev",
                8: "low_humidity",
                9: "eco_comfort",
            },
        },
        "FanSpeed": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "air_speed",
            "id2str": {
                0: "auto",
                1: "silent",
                2: "low",
                3: "moderate",
                4: "high",
            },
        },
        "MildewProof": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "mold_prev",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "ControlTone": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "sound_control",
            "id2str": {
                0: "silent",
                1: "button",
                2: "button+waterfull",
            },
        },
        "SaaControlTone": {  # currently not supported
            "controllable": False,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {},
        },
        "PowerConsumption": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "power_kwh",
        },
        "Ion": {  # currently not supported
            "controllable": False,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {},
        },
        "HumiditySetting": {
            "controllable": True,
            "is_numeric": True,
            "legacy_name": "target_humidity",
        },
        "AutoWindDirection": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "wind_swingable",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "KeypadLock": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {},
        },
        "DisplayBrightness": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "display_brightness",
            "id2str": {
                0: "bright",
                1: "dark",
                2: "off",
                3: "all_off",
            },
        },
        "FilterControl": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "air_cleaning_filter",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "PM25": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "pm25_value",
        },
        "IndoorHumidity": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "indoor_humidity",
        },
        "SideAirOutlet": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": "side_vent",
            "id2str": {
                0: "off",
                1: "on",
            },
        },
        "Defrost": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {},
        },
        "SmellIndex": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": "odor_level",
            "id2str": {
                0: "low",
                1: "middle",
                2: "high",
            },
        },
        "CleanFilterNotification": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": "clean_filter_notify",
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "TankFullNotification": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": "water_full_warning",
            "id2str": {
                0: "off",  # not activated
                1: "on",  # activated
            },
        },
        "TaiseiaError": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "Error": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "error_code",
        },
        "max_humidity": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "max_humidity",
        },
        "min_humidity": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": "min_humidity",
        },
    },
    "HE": {
        "DeviceType": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": "DeviceType",
            "id2str": {
                1: "AC",
                2: "DH",
                3: "HE",
                4: "PM25_PANEL",
            },
        },
        "Switch": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "off",
                1: "on",
            },
        },
        "Mode": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "air_condition",
                1: "dehumidification",
                2: "air_supply",
                3: "auto",
                4: "heater",
            },
        },
        "FanSpeed": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "auto",
                1: "silent",
                2: "low",
                3: "moderate",
                4: "high",
            },
        },
        "IndoorTemperature": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "TaiseiaError": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
        "CleanFilterNotification": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "BreathMode": {
            "controllable": True,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {0: "auto", 1: "energy_recovery", 2: "normal"},
        },
        "FrontFilterNotification": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "Pm25FilterNotification": {
            "controllable": False,
            "is_numeric": False,
            "legacy_name": None,
            "id2str": {
                0: "disabled",
                1: "enabled",
            },
        },
        "Error": {
            "controllable": False,
            "is_numeric": True,
            "legacy_name": None,
        },
    },
    "PM25_PANEL": {},
}


class JciHitachiAWSStatus:
    """Data class representing `AWSThing` status.

    Parameters
    ----------
    raw_status : dict
        Status retrieved from `JciHitachiAWSMqttConnection` _on_publish() callback.
    legacy : bool, optional
        Whether the raw_status is a legacy status, i.e. derived from subclasses of `JciHitachiStatus`, by default False.
    """

    device_type_mapping = {
        1: "AC",
        2: "DH",
        3: "HE",
        4: "PM25_PANEL",
    }

    def __init__(self, raw_status: dict, legacy=False) -> None:
        self._raw_status: dict = raw_status
        self._status: dict = raw_status if legacy else self._preprocess(raw_status)
        self._device_type: str = self._status["DeviceType"]

    def __getattr__(self, name):
        return self._status.get(name, "unsupported")

    def __repr__(self) -> str:
        return str(self._status)

    def _preprocess(self, raw_status):
        # device type
        if "DeviceType" not in raw_status or (
            "DeviceType" in raw_status
            and raw_status["DeviceType"] not in self.device_type_mapping
        ):
            raise AttributeError(
                "`DeviceType` isn't in the raw status or has an invalid value."
            )

        if "PowerConsumption" in raw_status:
            raw_status["PowerConsumption"] /= 10.0

        status = {}
        device_type = self.device_type_mapping[raw_status["DeviceType"]]
        for key, value in raw_status.items():
            if key in STATUS_DICT[device_type]:
                if STATUS_DICT[device_type][key]["is_numeric"]:
                    status[key] = value
                else:
                    status[key] = STATUS_DICT[device_type][key]["id2str"].get(
                        value, "unknown"
                    )

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
    def legacy_status(self):
        """All legacy status name used by the old API.

        Returns
        -------
        JciHitachiAWSStatus
            Status with legacy name.
        """

        status = {}
        device_type = self._status["DeviceType"]
        for status_name, status_value in self._status.items():
            if status_name in STATUS_DICT[device_type]:
                if STATUS_DICT[device_type][status_name]["legacy_name"] is None:
                    # no legacy name
                    status.update({status_name: status_value})
                else:
                    status.update(
                        {
                            STATUS_DICT[device_type][status_name][
                                "legacy_name"
                            ]: status_value
                        }
                    )
        return JciHitachiAWSStatus(status, legacy=True)

    @staticmethod
    @lru_cache
    def str2id(
        device_type: str,
        status_name: str,
        status_value: int = None,
        status_str_value: str = None,
        support_code: int = None,
    ):
        is_valid = (status_value is not None) ^ (status_str_value is not None)

        # Name check
        if is_valid:
            if status_name not in STATUS_DICT[device_type]:
                legacy2new = {
                    specs["legacy_name"]: new_status_name
                    for new_status_name, specs in STATUS_DICT[device_type].items()
                }
                if status_name in legacy2new:
                    status_name = legacy2new[status_name]
                else:
                    is_valid = False

        # Value check
        if is_valid:
            if status_str_value is not None:
                str2id_dict = {
                    value: key
                    for key, value in STATUS_DICT[device_type][status_name][
                        "id2str"
                    ].items()
                }
                if status_str_value in str2id_dict:
                    status_value = str2id_dict[status_str_value]
                else:
                    is_valid = False
            else:
                if (
                    not STATUS_DICT[device_type][status_name]["is_numeric"]
                    and status_value
                    not in STATUS_DICT[device_type][status_name]["id2str"]
                ):
                    is_valid = False

        # if support_code is specified, we check whether the given status value is valid for the device
        if is_valid and support_code is not None:
            if STATUS_DICT[device_type][status_name]["is_numeric"]:
                if status_value > support_code.status[status_name]:
                    is_valid = False
            else:
                if 2**status_value & support_code.status[status_name] == 0:
                    is_valid = False

        return is_valid, status_name, status_value

    def set_new_status(self, name: str, value: int):
        if STATUS_DICT[self._device_type][name]["is_numeric"]:
            self._status[name] = value
        else:
            self._status[name] = STATUS_DICT[self._device_type][name]["id2str"].get(
                value, "unknown"
            )


class JciHitachiAWSStatusSupport:
    """Data class representing `AWSThing` status support.

    Parameters
    ----------
    raw_status : dict
        Status retrieved from `JciHitachiAWSMqttConnection` _on_publish() callback.
    """

    device_type_mapping = JciHitachiAWSStatus.device_type_mapping

    def __init__(self, raw_status: dict) -> None:
        self._raw_status: dict = raw_status
        self._status: dict = self._preprocess(raw_status)

    def __getattr__(self, name):
        return self._status.get(name, "unsupported")

    def __repr__(self) -> str:
        return str(self._status)

    def _preprocess(self, status):
        status = status.copy()

        if status.get("Error", 0) != 0:
            return status

        # device type
        status["DeviceType"] = self.device_type_mapping[status["DeviceType"]]

        status["Brand"] = "HITACHI"

        if status["DeviceType"] == "AC":
            status["max_temp"] = (
                status["TemperatureSetting"] & 255
                if "TemperatureSetting" in status
                else 32
            )
            status["min_temp"] = (
                status["TemperatureSetting"] >> 8 & 255
                if "TemperatureSetting" in status
                else 16
            )
        elif status["DeviceType"] == "DH":
            status["max_humidity"] = (
                status["HumiditySetting"] & 255 if "HumiditySetting" in status else 70
            )
            status["min_humidity"] = (
                status["HumiditySetting"] >> 8 & 255
                if "HumiditySetting" in status
                else 40
            )

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
