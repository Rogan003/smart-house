import time
import random

from colors import print_green


keys = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

def run_door_membrane_switch_simulator(delay, callback, stop_event, row, col, settings):
    time.sleep(delay)
    key = keys[row][col]
    callback(key, settings)
    print_green(f"[Door 1] - Key '{key}' pressed (membrane switch)")