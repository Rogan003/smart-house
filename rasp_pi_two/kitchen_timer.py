import threading

class KitchenTimer:
    def __init__(self, n=10):
        self.n = n
        self.current_time = n
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.current_time += self.n

    def decrement(self):
        with self.lock:
            if self.current_time > 0:
                self.current_time -= 1
            return self.current_time

    def get_time(self):
        with self.lock:
            return self.current_time

kitchen_timer = KitchenTimer(n=10)
