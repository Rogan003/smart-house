from colors import print_gray


def buzz(callback):
    callback()
    print_gray("Door Buzzer One - Buzzing")

def run_door_buzzer_one_simulator(callback):
    buzz(callback)