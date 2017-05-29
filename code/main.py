#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse
import plan
from plan import Plan

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

parser.add_argument('--nodes'
                    , default=10
                    , type=check_positive
                    , help='Number of Bitcoin nodes spawned.'
                    )
parser.add_argument('--blocks'
                    , default=100
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
parser.add_argument('--selfish-nodes'
                    , default=0
                    , type=check_positive
                    , help='Number of selfish nodes spawned'
                    )
parser.add_argument('--connectivity'
                    , type=check_percentage
                    , help='Number of nodes the selfish nodes are connected to'
                    )
parser.add_argument('--lead-stubborn'
                    , help='use lead-stubbornness in strategy'
                    , action='store_const'
                    , const=True
                    )
parser.add_argument('--equal-fork-stubborn'
                    , help='use equal-fork-stubbornness in strategy'
                    , action='store_const'
                    , const=True
                    )
parser.add_argument('--trail-stubborn'
                    , help='use N-trail-stubbornness in strategy'
                    , type=check_positive
                    )

args = parser.parse_args()


def run():
    if args.selfish_nodes == 0:
        if args.connectivity is not None or args.lead_stubborn is not None or args.equal_fork_stubborn is not None or \
                        args.trail_stubborn is not None:
            parser.error('when selfish_nodes is 0 no selfish mining settings should be set')

    if os.system("docker inspect " + plan.node_image + " > /dev/null") != 0:
        print("Image " + plan.node_image + " not found")
        exit()

    if os.system("docker inspect " + plan.selfish_node_image + " > /dev/null") != 0:
        print("Image " + plan.selfish_node_image + " not found")
        exit()

    print("arguments called with: {}".format(sys.argv))
    print("parsed arguments: {}".format(args))

    os.system("rm -rf " + plan.host_dir('*'))

    p = Plan(args)
    commands = p.create()

    if args.dry_run:
            print('\n'.join(commands))
    else:
        """ write execution plan to a file beforehand """
        with open("../data/execution-plan.sh", "w") as file:
            for command in commands:
                file.write(command)
                file.write("\n")
        """ execute plan line by line """
        for command in commands:
            print(command)
            os.system(command)

run()
