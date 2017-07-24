import time
import logging


def sleep(seconds):
    logging.debug("Sleep for {} seconds".format(seconds))
    time.sleep(seconds)


def check_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)


def get_non_negative_int(prompt):
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue

        if value < 0:
            print("Sorry, your response must be positive.")
            continue
        else:
            break
    return value


def get_percentage(prompt):
    while True:
        try:
            value = float(input(prompt))
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue

        if value < 0 or value > 1:
            print("Sorry, your response must be between 0 and 1.")
            continue
        else:
            break
    return value


def get_node_type(prompt):
    while True:
        try:
            value = str(input(prompt))
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue

        if value not in ['normal', 'selfish']:
            print("Sorry, I don't know this node type.")
            continue
        else:
            break
    return value


def get_boolean(prompt):
    while True:
        try:
            value = str.lower(str(input(prompt)))
        except ValueError:
            print("Sorry, I didn't understand that.")
            continue

        if value not in ['y', 'yes', 'no', 'n']:
            print("Sorry, please enter yes or no.")
            continue
        else:
            if value in ['y', 'yes']:
                value_to_boolean = True
            else:
                value_to_boolean = False
            break

    return value_to_boolean
