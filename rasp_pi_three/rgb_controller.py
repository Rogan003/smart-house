import threading

class RGBController:
    def __init__(self):
        self.color = "off"
        self.lock = threading.Lock()
        self._callback = None

    def set_callback(self, callback):
        self._callback = callback

    def set_color(self, color):
        with self.lock:
            self.color = color
        if self._callback:
            self._callback(color)

    def get_color(self):
        with self.lock:
            return self.color

rgb_controller = RGBController()
