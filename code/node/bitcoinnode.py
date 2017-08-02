import tccmd
import bash
from node.abstract import BitcoinNode
from node.abstract import PublicNode


class PublicBitcoinNode(BitcoinNode, PublicNode):
    def __init__(self, name, ip, latency):
        BitcoinNode.__init__(self, name, ip)
        PublicNode.__init__(self, latency)

    def add_latency(self, zones):
        for cmd in tccmd.create(self.name, zones, self.latency):
            bash.check_output(cmd)
