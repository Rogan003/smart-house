from colors import print_yellow

import time


def turn_diode_on():
    global turned_on
    turned_on = True
    print_yellow("Door Light ON")

def turn_diode_off():
    global turned_on
    turned_on = False
    print_yellow("Door Light OFF")


def toggle(callback):
    callback()
    turn_diode_on()
    time.sleep(1)
    turn_diode_off()

def run_door_led_light_simulator(callback):
    toggle(callback)