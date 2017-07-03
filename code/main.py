#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse
import config
from executor import Executor
import csv
import logging
import checkargs
import time
import pandas

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

    nodes = selfish_nodes = 0
    network_config = pandas.read_csv(open(config.network_config), skiprows=1, delimiter=';', index_col=0)
    for node_row, row in network_config.iterrows():
        if node_row.startswith(config.node_prefix):
            nodes += 1
        elif node_row.startswith(config.selfish_node_prefix):
            selfish_nodes += 1
        else:
            raise Exception('Unknown node type in {}'.format(config.network_config))
    logging.info('Parsed {} nodes and {} selfish nodes from {}'.format(nodes, selfish_nodes, config.network_config))

    executor = Executor(args, nodes, selfish_nodes)
    executor.execute()

run()
