from homeassistant.const import EVENT_HOMEASSISTANT_START, \
    EVENT_HOMEASSISTANT_STOP


class MockBus():
    def __init__(self, callbacks):
        self.callbacks = callbacks

    def listen_once(self, method, call_back):
        self.callbacks[method] = call_back


class MockHass():
    def __init__(self):
        self.callbacks = {}
        self.bus = MockBus(self.callbacks)

    def start_hass(self):
        _callback = self.callbacks[EVENT_HOMEASSISTANT_START]
        _callback(None)
