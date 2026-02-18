import threading

class BuzzerController:
    def __init__(self):
        self.active = False
        self.lock = threading.Lock()
        self._callback = None

    def set_callback(self, callback):
        self._callback = callback

    def turn_on(self):
        with self.lock:
            self.active = True
        if self._callback:
            self._callback(True)

    def turn_off(self):
        with self.lock:
            self.active = False
        if self._callback:
            self._callback(False)

    def is_active(self):
        with self.lock:
            return self.active

buzzer_controller = BuzzerController()
