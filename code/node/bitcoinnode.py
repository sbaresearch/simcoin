import tccmd
import bash
from node.abstract import BitcoinNode
from node.abstract import PublicNode
import utils
from node.abstract import AbstractNodeConfig
from node import abstract
import config


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip, latency):
        BitcoinNode.__init__(self, name, ip)
        PublicNode.__init__(self, latency)

    def add_latency(self):
        if self.latency > 0:
            return bash.check_output(tccmd.add(self.name, self.latency))


class BitcoinNodeConfig(AbstractNodeConfig):
    def __init__(self, name=None, share=None, latency=None):
        super().__init__(name, share, latency)


def create_bitcoin_config():
    amount = utils.get_non_negative_int('How many normal nodes do you want create?\n> ')
    nodes = []

    for i in range(amount):
        node = BitcoinNodeConfig()
        node.name = config.node_name.format(i)

        print('{}. Node'.format(i+1))

        node = abstract.create_config(node)

        nodes.append(node)
    return nodes
