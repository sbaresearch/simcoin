#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse
import config
from executor import Executor
import logging
import checkargs
import time
from stats import Stats
from event import Event
import utils


def main():

    for file in [config.network_config, config.interval_csv, config.nodes_config_json]:
        if not os.path.isfile(file):
            raise Exception("{} file not found. Please generate file before starting Simcoin.".format(file))

    interval_duration = utils.get_non_negative_int('How long should one interval last? [s]\n> ')

    verbose = utils.get_boolean('Should the logging be verbose? [yes/no]\n> ')
    config_logger(verbose)

    executor = Executor()

    stats = Stats(executor)
    executor.stats = stats

    event = Event(executor, interval_duration)
    executor.event = event

    start = time.time()

    executor.execute()

    logging.info("the duration of the experiment was {} seconds".format(str(time.time() - start)))


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

if __name__ == "__main__":
    main()
