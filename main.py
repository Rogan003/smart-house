import threading

from components.door_button_one import run_door_button_one
from components.door_led_light import run_door_led_lights

from settings import load_settings
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    try:
        door_button_one_settings = settings['door_button_one']
        run_door_button_one(door_button_one_settings, threads, stop_event)

        door_led_light_settings = settings['door_led_light']
        run_door_led_lights(door_led_light_settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()
