#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import config
from executor import Executor
import logging
import time
from stats import Stats
from event import Event
import utils
import nodesconfig
import intervals
import networktopology
import sys
import argparse


def create_nodes():
    nodesconfig.create()


def create_intervals():
    intervals.create()


def create_networktopology():
    networktopology.parse()


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

commands = {
    'nodes':        nodesconfig.create,
    'network':      networktopology.create,
    'intervals':    intervals.create,
    'simulate':     run_simulation,
    'run':          run,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simcoin a cryptocurrency simulator.',
        usage='''git <command> [<args>]

        The most commonly used git commands are:
        network
        intervals
        nodes
        simulate
        run
        ''')

    parser.add_argument('command', help='Subcommand to run')
    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])
    if args.command not in commands:
        print('Unrecognized command')
        parser.print_help()
        exit(1)
    # use dispatch pattern to invoke method with same name
    commands[args.command]()
