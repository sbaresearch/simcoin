#!/usr/bin/env python
# -*- coding: utf-8 -*-
import nodesconfig
import intervals
import networktopology
import sys
import argparse
import simulation


def run():
    nodesconfig.create()

    intervals.create()

    networktopology.create()

    simulation.run()

commands = {
    'nodes':        nodesconfig.create,
    'network':      networktopology.create,
    'intervals':    intervals.create,
    'simulate':     simulation.run,
    'run':          run,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Simcoin a cryptocurrency simulator.',
        usage='''git <command> [<args>]

        The commands are:
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
