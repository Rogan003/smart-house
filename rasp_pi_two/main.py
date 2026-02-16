import threading

from components.door_button_two import run_door_button_two
from components.door_motion_sensor_two import run_door_motion_sensor_two
from components.door_ultrasonic_sensor_two import run_door_ultrasonic_sensor_two
from components.kitchen_button import run_kitchen_button
from components.kitchen_dht import run_kitchen_dht
from components.kitchen_segment_display import run_kitchen_segment_display
from components.gyroscope import run_gyroscope

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
        door_button_two_settings = settings['door_button_two']
        run_door_button_two(door_button_two_settings, threads, stop_event)

        door_motion_sensor_two_settings = settings['door_motion_sensor_two']
        run_door_motion_sensor_two(door_motion_sensor_two_settings, threads, stop_event)

        door_ultrasonic_sensor_two_settings = settings['door_ultrasonic_sensor_two']
        run_door_ultrasonic_sensor_two(door_ultrasonic_sensor_two_settings, threads, stop_event)

        kitchen_dht_settings = settings['kitchen_dht']
        run_kitchen_dht(kitchen_dht_settings, threads, stop_event)

        kitchen_segment_display_settings = settings['kitchen_segment_display']
        run_kitchen_segment_display(kitchen_segment_display_settings, threads, stop_event)

        gyroscope_settings = settings['kitchen_gyroscope']
        run_gyroscope(gyroscope_settings, threads, stop_event)

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()