import threading

from components.door_button_one import run_door_button_one
from components.door_buzzer_one import run_door_buzzer_one
from components.door_led_light import run_door_led_lights
from components.door_motion_sensor import run_door_motion_sensor_one
from components.door_ultrasonic_sensor_one import run_door_ultrasonic_sensor_one

from settings import load_settings
import time


try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass

def menu(settings, threads, stop_event):
    door_led_light_settings = settings['door_led_light']
    door_buzzer_one_settings = settings['door_buzzer']

    while True:
        print("\n---- Menu ----")
        print("1. toggle door light")
        print("2. buzz\n")

        user_input = input("Enter command: ")
        if user_input == "1":
            run_door_led_lights(door_led_light_settings, threads, stop_event)
        elif user_input == "2":
            run_door_buzzer_one(door_buzzer_one_settings, threads, stop_event)
        else:
            print("Oops, invalid command!\n")
        print()


if __name__ == "__main__":
    print('Starting app')
    settings = load_settings()
    threads = []
    stop_event = threading.Event()

    try:
        door_motion_sensor_one_settings = settings['door_button_one']
        run_door_button_one(door_motion_sensor_one_settings, threads, stop_event)

        door_motion_sensor_one_settings = settings['door_motion_sensor_one']
        run_door_motion_sensor_one(door_motion_sensor_one_settings, threads, stop_event)

        door_ultrasonic_sensor_one_settings = settings['door_ultrasonic_sensor_one']
        run_door_ultrasonic_sensor_one(door_ultrasonic_sensor_one_settings, threads, stop_event)

        menu(settings, threads, stop_event)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print('Stopping app')
        for t in threads:
            stop_event.set()