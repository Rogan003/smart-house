import time
import random

from colors import print_white


def run_door_button_two_simulator(delay, settings, callback, stop_event):
    door_is_open = False
    
    while not stop_event.is_set():
        time.sleep(delay)
        
        if stop_event.is_set():
            break
        
        if not door_is_open:
            # 15% chance to open the door every cycle
            if random.randint(0, 100) <= 15:
                door_is_open = True
                callback(settings, "TRUE")
                
                # wait random time (2-10 seconds) before closing
                close_delay = random.uniform(2, 10)
                time.sleep(close_delay)
                
                if stop_event.is_set():
                    break
                
                door_is_open = False
                callback(settings, "FALSE")
