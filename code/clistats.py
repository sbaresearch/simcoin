import logging
from bitcoinrpc.authproxy import JSONRPCException
import utils
import config


class CliStats:
    def __init__(self, context, writer):
        self.context = context
        self.writer = writer

    def execute(self):
        self.persist_consensus_chain()
        self.persist_node_stats()

        logging.info('Executed cli stats')

    def persist_consensus_chain(self):
        height = self.context.first_block_height
        nodes = self.context.all_bitcoin_nodes.values()
        consensus_chain = []
        while True:
            blocks = []
            for node in nodes:
                try:
                    blocks.append(node.execute_rpc('getblockhash', height))
                except JSONRPCException:
                    break
            if len(blocks) == len(nodes) and utils.check_equal(blocks):
                consensus_chain.append(blocks[0])
                height += 1
            else:
                break
        write_consensus_chain(consensus_chain)
        logging.info('Persisted {} block long consensus chain from height={} and {} nodes'
                     .format(len(consensus_chain), height, len(nodes)))

    def persist_node_stats(self):
        tips = []
        for node in self.context.all_bitcoin_nodes.values():
            tips.extend([Tip.from_dict(node.name, chain_tip) for chain_tip in node.execute_rpc('getchaintips')])

        self.writer.write_csv(Tip.file_name, Tip.csv_header, tips)
        logging.info('Collected and persisted {} tips'.format(len(tips)))


def write_consensus_chain(chain):
    with open(config.consensus_chain_csv, 'w') as file:
        file.write('hash\n')
        file.writelines('\n'.join(chain))
        file.write('\n')


class Tip:
    csv_header = ['node', 'status', 'branchlen']
    file_name = 'tips.csv'

    def __init__(self, node, status, branchlen):
        self.node = node
        self.status = status
        self.branchlen = branchlen

    @classmethod
    def from_dict(cls, node, chain_tip):
        return cls(node, chain_tip['status'], chain_tip['branchlen'])

    def vars_to_array(self):
        return [self.node, self.status, self.branchlen]
