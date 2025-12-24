from colors import print_blue


def buzz(callback):
    callback()
    print_blue("[Door 1] - Buzzer Buzzing")

def run_door_buzzer_one_simulator(callback):
    buzz(callback)