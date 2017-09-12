import config
import utils
import logging
from bitcoinrpc.authproxy import JSONRPCException
import csv


class CliStats:
    def __init__(self, context):
        self.context = context

    def execute(self):
        self.save_consensus_chain()
        self.save_chains()
        self.node_stats()

        logging.info('Executed cli stats')

    def save_consensus_chain(self):
        with open(config.consensus_chain_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['height', 'block_hash'])
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
                    w.writerow([height, blocks[0]])
                    height += 1
                else:
                    break

    def save_chains(self):
        with open(config.chains_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['node', 'block_hashes'])
            for node in self.context.all_bitcoin_nodes.values():
                height = int(node.execute_rpc('getblockcount'))
                hashes = []
                while self.context.first_block_height <= height:
                    hashes.append(str(node.execute_rpc('getblockhash', height)))
                    height -= 1
                row = [node.name]
                row.extend(hashes)
                w.writerow(row)

    def node_stats(self):
        for node in self.context.all_bitcoin_nodes.values():
            tips = node.execute_rpc('getchaintips')

            for tip in tips:
                self.context.tips.append(Tip(node.name, tip['status'], tip['branchlen']))


class Tip:
    def __init__(self, node, status, branchlen):
        self.node = node
        self.status = status
        self.branchlen = branchlen

    @staticmethod
    def csv_header():
        return ['node', 'status', 'branchlen']

    def vars_to_array(self):
        return [self.node, self.status, self.branchlen]
