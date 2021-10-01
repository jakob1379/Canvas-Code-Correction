BOLD = '\033[1m'
ENDC = '\033[0m'
FAIL = '\033[91m'
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
UNDERLINE = '\033[4m'
WARNING = '\033[93m'


def header(string):
    return f"{HEADER}{string}{ENDC}"


def okblue(string):
    return f"{OKBLUE}{string}{ENDC}"


def okgreen(string):
    return f"{OKGREEN}{string}{ENDC}"


def warning(string):
    return f"{WARNING}{string}{ENDC}"


def fail(string):
    return f"{FAIL}{string}{ENDC}"


def bold(string):
    return f"{BOLD}{string}{ENDC}"


def underline(string):
    return f"{UNDERLINE}{string}{ENDC}"
