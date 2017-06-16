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

args = parser.parse_args()

logFormatter = logging.Formatter("%(asctime)s.%(msecs)03d000 [%(threadName)-12.12s] "
                                 "[%(levelname)-5.5s]  %(message)s", "%Y-%m-%d %H:%M:%S")
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler("debug.log", mode='w')
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
    for index, row in enumerate(csv.reader(open(config.network_config), delimiter=';')):
        if index >= 2:
            break
        if index == 0:
            nodes = int(row[1])
        elif index == 1:
            selfish_nodes = int(row[1])

    executor = Executor(args, nodes, selfish_nodes)
    executor.execute()

run()
