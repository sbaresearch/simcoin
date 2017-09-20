import utils
import logging
from bitcoinrpc.authproxy import JSONRPCException


class CliStats:
    def __init__(self, context):
        self.context = context

    def execute(self):
        self.save_consensus_chain()
        self.node_stats()

        logging.info('Executed cli stats')

    def save_consensus_chain(self):
        height = self.context.first_block_height
        nodes = self.context.all_bitcoin_nodes.values()
        while True:
            blocks = []
            for node in nodes:
                try:
                    blocks.append(node.execute_rpc('getblockhash', height))
                except JSONRPCException:
                    break
            if len(blocks) == len(nodes) and utils.check_equal(blocks):
                self.context.consensus_chain.append(blocks[0])
                height += 1
            else:
                break

    def node_stats(self):
        for node in self.context.all_bitcoin_nodes.values():
            tips = node.execute_rpc('getchaintips')

            for tip in tips:
                self.context.tips.append(Tip(node.name, tip['status'], tip['branchlen']))


class Tip:
    csv_header = ['node', 'status', 'branchlen']

    def __init__(self, node, status, branchlen):
        self.node = node
        self.status = status
        self.branchlen = branchlen

    def vars_to_array(self):
        return [self.node, self.status, self.branchlen]
