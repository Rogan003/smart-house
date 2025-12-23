from colors import print_gray, print_yellow

import threading
import time

#import RPi.GPIO as GPIO


turned_on = False

def turn_diode_on(settings):
    global turned_on

    if settings['simulated']:
        turned_on = True
        print_yellow("Door Light ON")
    else:
        #GPIO.output(settings['pin'], GPIO.HIGH)
        pass

def turn_diode_off(settings):
    global turned_on

    if settings['simulated']:
        turned_on = False
        print_yellow("Door Light OFF")
    else:
        #GPIO.output(settings['pin'], GPIO.LOW)
        pass


def run_door_led_lights(settings, threads, stop_event, turn_on=None):
    if settings['simulated']:
        if turned_on:
            turn_diode_off(settings)
        else:
            turn_diode_on(settings)

    else:
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(settings['pin'], GPIO.OUT)
        pass
