#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import setup

if sys.version_info <= (3,0):
    print("Sorry, requires Python 3.x or above")
    sys.exit(1)


parser = argparse.ArgumentParser(description='Running Simcoin. A Bitcoin Network Simulator.')

parser.add_argument('--nodes'
                    , default=2
                    , type=int
                    , help='Number of Bitcoin Nodes spawned.'
                    )
parser.add_argument('--blocks'
                    , default=1
                    , type=int
                    , help='Number of Blocks to be generated.'
                    )
parser.add_argument('--dryRun'
                    , default=False
                    , help='If true only prints the Bash script without execution'
                    )

args = parser.parse_args()

setup.run(args.dryRun, args.nodes, args.blocks)
