import dockercmd
import config
from node import PublicBitcoinNode
from node import SelfishPrivateNode
from node import ProxyNode
import logging
import bash
import prepare
import utils
from simulationfiles import network_config
from simulationfiles import nodes_config
from simulationfiles.zone import Zone


class Context:
    def __init__(self):
        self.args = utils.read_json_file(config.args_json)
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

    def create(self):
        self.config_nodes = nodes_config.read()
        nodes = [node for node in self.config_nodes if node.node_type == 'bitcoin']
        selfish_nodes = [node for node in self.config_nodes if node.node_type == 'selfish']

        self.nodes = {node.name: PublicBitcoinNode(node.name, self.zone.get_ip(node.latency),
                                                   node.latency, node.docker_image) for node in nodes}

        self.selfish_node_private_nodes = {}
        self.selfish_node_proxies = {}
        for node in selfish_nodes:
            ip_private_node = self.zone.get_ip(node.latency)
            ip_proxy = self.zone.get_ip(node.latency)
            self.selfish_node_private_nodes[node.name] = SelfishPrivateNode(node.name,
                                                                            ip_private_node, node.docker_image)

            self.selfish_node_proxies[node.name_proxy] = \
                ProxyNode(node.name_proxy, ip_proxy, ip_private_node, node.selfish_nodes_args,
                          node.latency, node.docker_image)

        self.all_bitcoin_nodes = dict(self.nodes, **self.selfish_node_private_nodes)

        self.all_public_nodes = dict(self.nodes, **self.selfish_node_proxies)
        self.all_nodes = dict(self.nodes, **self.selfish_node_private_nodes, **self.selfish_node_proxies)

        self.one_normal_node = next(iter(self.nodes.values()))

        connections = network_config.read_connections()
        for node in self.all_public_nodes.values():
            node.outgoing_ips = [str(self.all_public_nodes[connection].ip) for connection in connections[node.name]]
