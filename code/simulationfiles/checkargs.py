import argparse


def check_positive(value):
    if value < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive value" % value)
    return value


def check_percentage(value):
    float_value = float(value)
    if float_value < 0 or float_value > 1:
        raise argparse.ArgumentTypeError("%s is an invalid percentage value [0,1]" % value)
    return float_value


def check_positive_float(value):
    float_value = float(value)
    check_positive(float_value)
    return float_value


def check_positive_int(value):
    int_value = int(value)
    if str(int_value) != value:
        raise argparse.ArgumentTypeError("%s is an invalid integer" % value)
    check_positive(int_value)
    return int_value
