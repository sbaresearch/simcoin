import time
import logging
import config
import sys
import os
import re
import numpy as np


def sleep(seconds):
    logging.debug("Sleep for {} seconds".format(seconds))
    time.sleep(seconds)


def check_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)


def config_logger(verbose):
    log_formatter = logging.Formatter("%(asctime)s.%(msecs)03d000 simcoin [%(threadName)-12.12s] "
                                      "[%(levelname)-5.5s]  %(message)s", "%Y-%m-%d %H:%M:%S")
    logging.Formatter.converter = time.gmtime
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler(config.log_file, mode='w')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    if verbose:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


def check_for_file(file):
    if not os.path.isfile(file):
        command = re.split('\.|/', file)[-2]
        print("{} file not found. Please generate this with the command `python3 simcoin.py {} [args]."
              .format(file, command))
        exit(-1)


class Values:
    def __init__(self):
        self.values = []
        self.np_values = None
        self.stats = None

    @classmethod
    def from_array(cls, array):
        obj = cls()
        obj.values = array
        return obj

    def calc(self):
        self.np_values = np.array(self.values)
        self.stats = Stats.from_array(self.np_values)


class Stats:

    def __init__(self, count, median, std):
        self.count = count
        self.median = median
        self.std = std

    @classmethod
    def from_array(cls, array):
        count = len(array)
        if count == 0:
            median = float('nan')
            std = float('nan')
        else:
            median = np.median(array)
            std = np.std(array)
        return cls(count, median, std)
