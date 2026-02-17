import threading

from components.living_room_motion_sensor import run_living_room_motion_sensor
from components.bedroom_dht import run_bedroom_dht
from components.master_bedroom_dht import run_master_bedroom_dht

from settings import load_settings
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

def menu(settings, threads, stop_event):
    kitchen_button_settings = settings['kitchen_button']

    while True:
        print("\n---- Menu ----")
        print("1. click kitchen button")

        user_input = input("Enter command: ")

        if user_input == "1":
            run_kitchen_button(kitchen_button_settings, threads, stop_event)

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

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()