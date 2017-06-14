#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse
import config
from plan import Plan
import csv

if sys.version_info <= (3, 0):
    print("Sorry, requires Python 3.x or above")
    exit()


def check_percentage(value):
    float_value = float(value)
    if float_value < 0 or float_value > 1:
        raise argparse.ArgumentTypeError("%s is a percentage value and should be be in [0,1]" % value)
    return float_value


def check_positive(value):
    integer_value = int(value)
    if integer_value < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return integer_value

parser = argparse.ArgumentParser(description='Running Simcoin. A Bitcoin Network Simulator.')

parser.add_argument('--blocks'
                    , default=20
                    , type=check_positive
                    , help='Number of blocks to be generated.'
                    )
parser.add_argument('--block-interval'
                    , default=10
                    , type=check_positive
                    , help='Targeted block interval time in seconds.'
                    )
parser.add_argument('--latency'
                    , default=100
                    , type=check_positive
                    , help='Network latency on all connections.'
                    )
parser.add_argument('--dry-run'
                    , action='store_true'
                    , help='If true only prints the bash script without execution'
                    )
parser.add_argument('--selfish-nodes-args'
                    , help='Set args for selfish nodes. '
                           'Set them as string and if you use just one add a space at the end. Eg.: "--arg "'
                    , default=''
                    )

args = parser.parse_args()


def run():
    for image in [config.node_image, config.selfish_node_image]:
        if os.system("docker inspect " + image + " > /dev/null") != 0:
            print("Image " + image + " not found")
            exit()

    for file in [config.network_config]:
        if not os.path.isfile(file):
            print(file + " file not found. Please generate file before starting Simcoin.")
            exit()

    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))

    nodes = selfish_nodes = 0
    for index, row in enumerate(csv.reader(open(config.network_config), delimiter=';')):
        if index >= 2:
            break
        if index == 0:
            nodes = int(row[1])
        elif index == 1:
            selfish_nodes = int(row[1])

    p = Plan(args, nodes, selfish_nodes)
    commands = p.create()

    if args.dry_run:
            print('\n'.join(commands))
    else:
        """ write execution plan to a file beforehand """
        with open("../data/execution-plan.sh", "w") as file:
            file.write("#!/usr/bin/env bash\n")
            for command in commands:
                file.write(command)
                file.write("\n")
        """ execute plan line by line """
        for command in commands:
            print(command)
            os.system("/bin/bash -c '{}'".format(command))

run()
