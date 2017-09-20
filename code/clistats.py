import utils
import logging
from bitcoinrpc.authproxy import JSONRPCException
import utils


class CliStats:
    def __init__(self, context):
        self.context = context

    def execute(self):
        self.persist_consensus_chain()
        self.node_stats()

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

        with open(self.context.path.consensus_chain_csv, 'w') as file:
            file.write('hash\n')
            file.writelines('\n'.join(consensus_chain))
            file.write('\n')

    def node_stats(self):
        tips = []
        for node in self.context.all_bitcoin_nodes.values():
            tips.extend(node.execute_rpc('getchaintips'))

        utils.write_csv(Tip.file_name, Tip.csv_header, tips, self.context.args.tag)


class Tip:
    csv_header = ['node', 'status', 'branchlen']
    file_name = 'tips.csv'

    def __init__(self, node, status, branchlen):
        self.node = node
        self.status = status
        self.branchlen = branchlen

    def vars_to_array(self):
        return [self.node, self.status, self.branchlen]
