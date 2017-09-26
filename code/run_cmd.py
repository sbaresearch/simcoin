from simulationfiles import nodes_config
from simulationfiles import ticks_config
from simulationfiles import network_config
import simulation_cmd
import argparse
import utils
import logging
import sys
from simulationfiles import checkargs


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--verbose'
                        , action="store_true"
                        , help='Verbose log.'
                        )

    parser.add_argument('--tag'
                        , default='run'
                        , help='A tag that will be added to every csv file.'
                        )

    args = parser.parse_known_args(sys.argv[2:])[0]
    utils.update_args_json(args)
    return args


def run(tag_appendix=None):
    args = parse_args()
    logging.info("Parsed arguments in {}: {}".format(__name__, args))

    if tag_appendix:
        args.tag = args.tag + tag_appendix
    utils.update_args_json(args)

    nodes_config.create(unknown_arguments=True)

    ticks_config.create(unknown_arguments=True)

    network_config.create(unknown_arguments=True)

    simulation_cmd.run()
