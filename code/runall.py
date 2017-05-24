#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import argparse
import setup

if sys.version_info <= (3, 0):
    print("Sorry, requires Python 3.x or above")
    sys.exit(1)


def check_positive(value):
    integer_value = int(value)
    if integer_value < 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return integer_value

parser = argparse.ArgumentParser(description='Running Simcoin. A Bitcoin Network Simulator.')

parser.add_argument('--nodes'
                    , default=2
                    , help='Number of Bitcoin Nodes spawned.'
                    , type=check_positive
                   )
parser.add_argument('--blocks'
                    , default=100
                    , help='Number of Blocks to be generated.'
                    , type=check_positive
                   )
parser.add_argument('--block-time'
                    , default=10
                    , type=check_positive
                    , help='Targeted generation time in seconds.'
                   )
parser.add_argument('--latency'
                    , default=100
                    , type=check_positive
                    , help='Network latency on all connections.'
                   )
parser.add_argument('--dry-run'
                    , action='store_true'
                    , help='If true only prints the Bash script without execution'
                   )

args = parser.parse_args()


def run(dry_run, nodes, blocks, block_time, latency):
    print("input: ", dry_run, nodes, blocks, block_time, latency)
    plan = setup.executionPlan(nodes, blocks, block_time, latency)

    if dry_run:
            print('\n'.join(plan))
    else:
        """ write execution plan to a file beforehand """
        with open("../data/execution-plan.sh", "w") as file:
            for line in plan:
                file.write(line)
                file.write("\n")
        """ execute plan line by line """
        for cmd in plan:
            print(cmd)
            os.system(cmd)

run(args.dry_run, args.nodes, args.blocks, args.block_time, args.latency)
