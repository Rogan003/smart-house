from colors import print_red


def click(callback, settings):
    callback(settings)
    print_red("[Kitchen Button] - Clicked")

def run_kitchen_button_simulator(settings, callback):
    click(callback, settings)
