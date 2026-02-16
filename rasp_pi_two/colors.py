class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BROWN = '\033[33m'
    WHITE = '\033[97m'
    GRAY = '\033[37m'
    RESET = '\033[0m' # reset color

def print_red(text):
    print(Colors.RED + text + Colors.RESET)

def print_green(text):
    print(Colors.GREEN + text + Colors.RESET)

def print_yellow(text):
    print(Colors.YELLOW + text + Colors.RESET)

def print_blue(text):
    print(Colors.BLUE + text + Colors.RESET)

def print_magenta(text):
    print(Colors.MAGENTA + text + Colors.RESET)

def print_brown(text):
    print(Colors.BROWN + text + Colors.RESET)

def print_white(text):
    print(Colors.WHITE + text + Colors.RESET)

def print_gray(text):
    print(Colors.GRAY + text + Colors.RESET)