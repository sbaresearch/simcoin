import time
import logging
import config
import sys
import os
import re
from collections import namedtuple
import csv
from ast import literal_eval


def sleep(seconds):
    logging.debug("Sleep for {} seconds".format(seconds))
    time.sleep(seconds)


def check_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)


def config_logger(verbose):
    log_formatter = logging.Formatter("%(asctime)s.%(msecs)03d000 [%(processName)s-%(threadName)-12.12s] "
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


def read_csv(file_name):
    if os.path.isfile(file_name):
        with open(file_name, 'r') as file:
            try:
                reader = csv.reader(file)
                Args = namedtuple("Args", next(reader))
                line = next(reader)
                for i, var in enumerate(line):
                    try:
                        line[i] = literal_eval(var)
                    except ValueError:
                        pass
                return Args._make(line)
            except StopIteration:
                logging.debug('File={} has not enough lines'.format(config.args_csv))
                return None


def update_args(args):
    persisted_args = {}
    persisted_tuple = read_csv(config.args_csv)
    if persisted_tuple:
        persisted_args = dict(persisted_tuple._asdict())

    data = {**persisted_args, **vars(args)}
    cleaned_data = {k: v for k, v in data.items() if v is not None}
    with open(config.args_csv, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(cleaned_data.keys())
        writer.writerow(cleaned_data.values())


def json_object_hook(d):
    return namedtuple('X', d.keys())(*d.values())
