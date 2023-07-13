import time
import httpx
import logging
import hashlib

ENDPOINT = "https://www.google-analytics.com/mp/collect"
API_SECRET = "N_ckE4wvQk2rIVmjJDs8DA"
MEASUREMENT_ID = "G-KCX17MWQZG"
GRAIN_SIZE = 60 # 30 mins if an event is generated every 30 seconds.

_LOGGER = logging.getLogger(__name__)

class AnalyticsRecorder:
    """AnalyticsRecorder reporting events to Analytics.

    Parameters
    ----------
    identifier : str
        User identifier.
    event_name : str
        Event name that will be uploaded to Analytics.
    debug : bool
        If debug, the grain size will be 1.
    timeout : float
        The http request timeout.
    """

    events = []
    def __init__(self, identifier, event_name, debug=False, timeout=2):
        self.identifier = hashlib.sha256(identifier.encode("utf8")).hexdigest()
        self.event_name = event_name
        self.debug = debug
        self.timeout = timeout
        self.failures = 0
        self._event = {}

    def _send(self):
        try:
            _LOGGER.debug("Uploading data to Analytics.")
            httpx.request(
                "post",
                ENDPOINT,
                params={"api_secret": API_SECRET, "measurement_id": MEASUREMENT_ID},
                json={
                    "client_id": self.identifier,
                    "events": [
                        {
                            "name": self.event_name,
                            "params": {
                                "items": AnalyticsRecorder.events,
                            }
                        }
                    ]
                },
                timeout=self.timeout
            )
        except:
            _LOGGER.error(f"Failed to upload {self.event_name} events to Analytics.")
        AnalyticsRecorder.events.clear()

    def record(self, key, value):
        self._event[key] = value
        
    def record_time(self, key):
        self._event[f"{key}_time"] = time.perf_counter() - self.prev_elapsed

    def record_failure(self):
        self.failures += 1

    def __enter__(self):
        self.prev_elapsed = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.record("timestamp", time.time())
        AnalyticsRecorder.events.append(self._event)

        grain_size = 1 if self.debug else GRAIN_SIZE
        if len(AnalyticsRecorder.events) >= grain_size:
            self._send()