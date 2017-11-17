import config
from node import PublicBitcoinNode
import utils
from simulationfiles import network_config
from simulationfiles.zone import Zone
from collections import OrderedDict
import time


class Context:
    def __init__(self):
        self.run_name = 'run-' + str(time.time())
        self.run_dir = config.data_dir + self.run_name + '/'
        self.args = utils.read_args()
        self.zone = Zone()

        self.config_nodes = None

        self.nodes = None

        self.first_block_height = None
        self.step_times = []

    def create(self):
        nodes = utils.read_csv(config.nodes_csv)

        self.nodes = OrderedDict([])
        for node in nodes:
            self.nodes.update({node.name: PublicBitcoinNode(node.name, node.group,
                                                            self.zone.get_ip(node.latency),
                                                            node.latency, node.docker_image,
                                                            self.run_dir + node.name)})

        connections = network_config.read_connections()
        for node in self.nodes.values():
            node.outgoing_ips.extend(
                [str(self.nodes[connection].ip) for connection in connections[node.name]]
            )
