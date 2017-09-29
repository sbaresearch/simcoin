import config
from node import PublicBitcoinNode
from node import SelfishPrivateNode
from node import ProxyNode
import utils
from simulationfiles import network_config
from simulationfiles import nodes_config
from simulationfiles.zone import Zone
from collections import OrderedDict
from copy import copy
import time


class Context:
    def __init__(self):
        self.run_name = 'run-' + str(time.time())
        self.run_dir = config.data_dir + self.run_name + '/'
        self.args = utils.read_args()
        self.zone = Zone()

        self.config_nodes = None

        self.nodes = None
        self.selfish_node_private_nodes = None
        self.selfish_node_proxies = None
        self.all_bitcoin_nodes = None
        self.all_public_nodes = None
        self.all_nodes = None
        self.one_normal_node = None

        self.first_block_height = None
        self.step_times = []

    def create(self):
        self.config_nodes = utils.read_csv(config.nodes_csv)
        nodes = [node for node in self.config_nodes if node.node_type == 'bitcoin']
        selfish_nodes = [node for node in self.config_nodes if node.node_type == 'selfish']

        self.nodes = OrderedDict([])
        for node in nodes:
            self.nodes.update({node.name: PublicBitcoinNode(node.name, node.group,
                                                            self.zone.get_ip(node.latency),
                                                            node.latency, node.docker_image,
                                                            self.run_dir + node.name)})

        self.selfish_node_private_nodes = OrderedDict([])
        self.selfish_node_proxies = OrderedDict([])
        for node in selfish_nodes:
            ip_private_node = self.zone.get_ip(node.latency)
            ip_proxy = self.zone.get_ip(node.latency)

            self.selfish_node_private_nodes.update({node.name: SelfishPrivateNode(node.name, node.group,
                                                                                  ip_private_node,
                                                                                  config.standard_image,
                                                                                  self.run_dir + node.name)})
            name_proxy = node.name + '-proxy'
            selfish_args = None
            if hasattr(self.args, 'selfish_args'):
                selfish_args = self.args.selfish_args
            self.selfish_node_proxies.update({name_proxy: ProxyNode(name_proxy, node.group, ip_proxy,
                                                                    ip_private_node, selfish_args,
                                                                    node.latency, node.docker_image,
                                                                    self.run_dir + name_proxy)})

        self.all_bitcoin_nodes = copy(self.nodes)
        self.all_bitcoin_nodes.update(self.selfish_node_private_nodes)

        self.all_public_nodes = copy(self.nodes)
        self.all_public_nodes.update(self.selfish_node_proxies)

        self.all_nodes = copy(self.selfish_node_proxies)
        self.all_nodes.update(self.selfish_node_private_nodes)
        self.all_nodes.update(self.nodes)

        self.one_normal_node = next(iter(self.nodes.values()))

        connections = network_config.read_connections()
        for node in self.all_public_nodes.values():
            node.outgoing_ips = [str(self.all_public_nodes[connection].ip) for connection in connections[node.name]]
