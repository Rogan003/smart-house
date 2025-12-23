from colors import print_gray, print_yellow

import threading
import time

#import RPi.GPIO as GPIO


turned_on = False

def turn_diode_on(settings):
    global turned_on

    if settings['simulated']:
        if turned_on:
            return
        turned_on = True
        print_yellow("Door Light ON")
    else:
        #GPIO.output(settings['pin'], GPIO.HIGH)
        pass

def turn_diode_off(settings):
    global turned_on

    if settings['simulated']:
        if not turned_on:
            return
        turned_on = False
        print_yellow("Door Light OFF")
    else:
        #GPIO.output(settings['pin'], GPIO.LOW)
        pass


def run_door_led_lights(settings, threads, stop_event, turn_on=None):
    if settings['simulated']:
        while True:
            print("\n---- LED Diode ----")
            print("1. turn on door light")
            print("2. turn off door light\n")

            user_input = input("Enter command: ")
            if user_input == "1":
                turn_diode_on(settings)
            elif user_input == "2":
                turn_diode_off(settings)
            else:
                print("Oops, invalid command!\n")
            print()
    else:
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(settings['pin'], GPIO.OUT)
        pass
