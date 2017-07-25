#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import config
from executor import Executor
import logging
import time
from stats import Stats
from event import Event
import fire
import utils
import nodesconfig
import intervals
import networktopology


def create_nodes():
    nodesconfig.create()


def create_intervals():
    intervals.create()


def create_networktopology():
    networktopology.create()


def run():
    nodesconfig.create()

    intervals.create()

    networktopology.create()

    run_simulation()


def run_simulation():

    for file in [config.network_config, config.interval_csv, config.nodes_config_json]:
        if not os.path.isfile(file):
            raise Exception("{} file not found. Please generate file before starting Simcoin.".format(file))

    interval_duration = utils.get_non_negative_int('How long should one interval last? [s]\n> ')

    verbose = utils.get_boolean('Should the logging be verbose? [yes/no]\n> ')
    utils.config_logger(verbose)

    executor = Executor()

    stats = Stats(executor)
    executor.stats = stats

    event = Event(executor, interval_duration)
    executor.event = event

    start = time.time()

    executor.execute()

    logging.info("the duration of the experiment was {} seconds".format(str(time.time() - start)))


if __name__ == '__main__':
    fire.Fire()
