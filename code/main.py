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
import pandas
from stats import Stats
from prepare import Prepare

if sys.version_info <= (3, 0):
    print("Sorry, requires Python 3.x or above")
    exit()

parser = argparse.ArgumentParser(description='Running Simcoin. A Bitcoin Network Simulator.')

parser.add_argument('-v'
                    , '--verbose'
                    , help='Increase output verbosity'
                    , action='store_true'
                    )
parser.add_argument('--selfish-nodes-args'
                    , help='Set args for selfish nodes. '
                           'Set them as string and if you use just one add a space at the end. Eg.: "--arg "'
                    , default=''
                    )
parser.add_argument('--tick-duration'
                    , help='Set the duration of one tick in seconds.'
                    , default=1
                    , type=checkargs.check_positive_float
                    )

args = parser.parse_args()

logFormatter = logging.Formatter("%(asctime)s.%(msecs)03d000 executor [%(threadName)-12.12s] "
                                 "[%(levelname)-5.5s]  %(message)s", "%Y-%m-%d %H:%M:%S")
logging.Formatter.converter = time.gmtime
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler(config.log_file, mode='w')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

if args.verbose:
    rootLogger.setLevel(logging.DEBUG)
else:
    rootLogger.setLevel(logging.INFO)


def run():
    for image in [config.node_image, config.selfish_node_image]:
        if os.system("docker inspect " + image + " > /dev/null") != 0:
            logging.error("Image " + image + " not found")
            exit()

    for file in [config.network_config, config.tick_csv]:
        if not os.path.isfile(file):
            logging.error(file + " file not found. Please generate file before starting Simcoin.")
            exit()

    logging.info("arguments called with: {}".format(sys.argv))
    logging.info("parsed arguments: {}".format(args))

    executor = Executor(args)

    stats = Stats(executor)
    executor.stats = stats

    prepare = Prepare(executor)
    executor.prepare = prepare

    executor.execute()

run()
