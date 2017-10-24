from simulationfiles import nodes_config
from simulationfiles import ticks_config
from simulationfiles import network_config
import simulation_cmd


def run():
    nodes_config.create(unknown_arguments=True)
    ticks_config.create(unknown_arguments=True)
    network_config.create(unknown_arguments=True)

    simulation_cmd.run(unknown_arguments=True)
