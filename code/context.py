import config
from node import PublicBitcoinNode
import utils
from simulationfiles import network_config
from simulationfiles.zone import Zone
from collections import OrderedDict
import time


class Context:
    def __init__(self):
        self._run_name = 'run-' + str(time.time())
        self._run_dir = config.data_dir + self._run_name + '/'
        self._args = utils.read_args()
        self._zone = Zone()

        self._first_block_height = None
        self._step_times = []

        node_configs = utils.read_csv(config.nodes_csv)
        self._nodes = OrderedDict([])

        for node_config in node_configs:
            self.nodes.update({node_config.name: PublicBitcoinNode(
                node_config.name, node_config.group,
                self.zone.get_ip(node_config.latency),
                node_config.latency, node_config.docker_image,
                self.run_dir + node_config.name)})

        connections = network_config.read_connections()
        for node in self.nodes.values():
            node.set_outgoing_ips(
                [self.nodes[connection].ip for connection in connections[node.name]]
            )


    @property
    def run_name(self):
        return self._run_name

    @property
    def run_dir(self):
        return self._run_dir

    @property
    def args(self):
        return self._args

    @property
    def zone(self):
        return self._zone

    @property
    def nodes(self):
        return self._nodes

    @property
    def first_block_height(self):
        return self._first_block_height

    @first_block_height.setter
    def first_block_height(self, height):
        self._first_block_height = height

    @property
    def step_times(self):
        return self._step_times
