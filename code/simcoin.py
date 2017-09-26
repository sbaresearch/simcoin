#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from simulationfiles import nodes_config
from simulationfiles import ticks_config
from simulationfiles import network_config
import sys
import argparse
import simulation_cmd
import config
import os
import bitcoin
import utils
import multirun_cmd
import run_cmd
import logging
import bash

commands = {
    'nodes':        nodes_config.create,
    'network':      network_config.create,
    'ticks':        ticks_config.create,
    'simulate':     simulation_cmd.run,
    'run':          run_cmd.run,
    'multi-run':    multirun_cmd.run,
}


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--verbose'
                        , action="store_true"
                        , help='Verbose log.'
                        )

    args = parser.parse_known_args(sys.argv[2:])[0]
    utils.update_args(args)

    return args


def main():
    cmd_parser = argparse.ArgumentParser(
        description='Simcoin a cryptocurrency simulator.',
        usage='''<command> [<args>]

        The commands are:
        nodes       creates the {} for a simulation
        network     creates the {} for a simulation
        ticks       creates the {} for a simulation
        simulate    executes a simulation based on the {}, {} and {}
        run         runs all above commands
        multi-run   run the simulation multiple times
        '''.format(
            config.nodes_json_file_name,
            config.network_csv_file_name,
            config.ticks_csv_file_name,
            config.nodes_json_file_name,
            config.network_csv_file_name,
            config.ticks_csv_file_name,
        ))

    cmd_parser.add_argument('command', help='Subcommand to run')

    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = cmd_parser.parse_args(sys.argv[1:2])
    command = args.command
    if command not in commands:
        print('Unrecognized command')
        cmd_parser.print_help()
        exit(1)
    # use dispatch pattern to invoke method with same name

    if not os.path.exists(config.data_dir):
        os.makedirs(config.data_dir)

    bitcoin.SelectParams('regtest')

    args = parse_args()
    utils.config_logger(args.verbose)
    logging.info("Arguments called with: {}".format(sys.argv))
    logging.info("Parsed arguments in simcoin.py: {}".format(args))

    logging.info('Executing command={}'.format(command))
    commands[command]()


if __name__ == '__main__':
    main()
