from simulationfiles import nodes_config
from simulationfiles import ticks_config
from simulationfiles import network_config
import simulation_cmd
import argparse
import utils
import logging
import sys
from simulationfiles import checkargs


def run():
    nodes_config.create(unknown_arguments=True)

    ticks_config.create(unknown_arguments=True)

    network_config.create(unknown_arguments=True)

    simulation_cmd.run(unknown_arguments=True)
