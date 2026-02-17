import threading

from components.living_room_motion_sensor import run_living_room_motion_sensor
from components.bedroom_dht import run_bedroom_dht
from components.master_bedroom_dht import run_master_bedroom_dht
from components.living_room_display import run_living_room_display
from components.bedroom_rgb import run_bedroom_rgb
from components.bedroom_ir import run_bedroom_ir

from settings import load_settings
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

def menu(settings, threads, stop_event):
    bedroom_ir_settings = settings['bedroom_infrared']
    while True:
        print("\n---- Menu ----")
        print("1. Bedroom IR")

        user_input = input("Enter command: ")

        if user_input == "1":
            button = input("Enter button (0-7): ")
            run_bedroom_ir(bedroom_ir_settings, threads, stop_event, button)
        else:
            print("Oops, invalid command!\n")
        print()


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    try:
        bedroom_dht_settings = settings['bedroom_dht']
        run_bedroom_dht(bedroom_dht_settings, threads, stop_event)

        master_bedroom_dht_settings = settings['master_bedroom_dht']
        run_master_bedroom_dht(master_bedroom_dht_settings, threads, stop_event)

        living_room_motion_sensor_settings = settings['living_room_motion_sensor']
        run_living_room_motion_sensor(living_room_motion_sensor_settings, threads, stop_event)

        living_room_display_settings = settings['living_room_display']
        run_living_room_display(living_room_display_settings, threads, stop_event)

        bedroom_rgb_settings = settings['bedroom_rgb']
        run_bedroom_rgb(bedroom_rgb_settings, threads, stop_event)

        bedroom_ir_settings = settings['bedroom_infrared']
        if not bedroom_ir_settings['simulated']:
            run_bedroom_ir(bedroom_ir_settings, threads, stop_event)

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()