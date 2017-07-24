import tccmd
import bash
from node.abstract import BitcoinNode
from node.abstract import PublicNode
from node import abstract
import utils


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip):
        BitcoinNode.__init__(self, name, ip)
        PublicNode.__init__(self)

    def add_latency(self):
        if self.latency > 0:
            return bash.check_output(tccmd.add(self.name, self.latency))


def create_config():
    amount = utils.get_non_negative_int('How many normal nodes do you want create?\n> ')
    nodes = []

    for i in range(amount):
        node = {'type': 'normal'}

        print('{}. Node'.format(i+1))

        node = abstract.create_config(node)

        nodes.append(node)
    return nodes
