import time

from colors import print_yellow


def turn_diode_on():
    print_yellow("[Door 1] - Door Light ON")

def turn_diode_off():
    print_yellow("[Door 1] - Door Light OFF")

def run_door_led_light_simulator(callback, settings):
    callback(settings)
    turn_diode_on()
    time.sleep(1)
    turn_diode_off()