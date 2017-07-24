import tccmd
import bash
from node.abstract import BitcoinNode
from node.abstract import PublicNode


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip):
        BitcoinNode.__init__(self, name, ip)
        PublicNode.__init__(self)

    def add_latency(self):
        if self.latency > 0:
            return bash.check_output(tccmd.add(self.name, self.latency))
