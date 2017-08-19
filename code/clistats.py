import config
import utils
import operator
import logging
from utils import Values
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
        with open(config.nodes_csv, 'w') as file:
            file.write('name;'
                       'headers_only;headers_only_median_branchlen;headers_only_std_branchlen;'
                       'total_tips;total_tips_median_branchlen;tips_std_branchlen;'
                       'valid_fork;valid_fork_median_branchlen;valid_fork_std_branchlen;'
                       'valid_headers;valid_headers_median_branchlen;valid_headers_std_branchlen;\n')
            for node in self.context.all_bitcoin_nodes.values():
                file.write('{}'.format(node.name))

                tips = node.execute_rpc('getchaintips')
                tips_stats = tips_statistics(tips)
                sorted_tips_stats = sorted(tips_stats.items(), key=operator.itemgetter(0))

                for tip_stats_tuple in sorted_tips_stats:
                    tip_stats = tip_stats_tuple[1]
                    file.write(';{};{};{}'.format(tip_stats.stats.count, tip_stats.stats.median, tip_stats.stats.std))
                file.write('\n')


tip_types = ['headers-only', 'valid-fork', 'valid-headers']


def tips_statistics(tips):
    tip_stats = {tip_type: Values() for tip_type in tip_types}

    for tip in tips:
        if tip['status'] == 'active':
            # omit active tip
            pass
        else:
            try:
                tip_stats[tip['status']].values.append(tip['branchlen'])
            except KeyError:
                logging.error('Unknown tip type={}'.format(tip['status']))
                exit(-1)

    all_values = []
    for _, tip_stat in tip_stats.items():
        all_values.extend(tip_stat.values)
    tip_stats['total'] = Values.from_array(all_values)

    for _, tip_stat in tip_stats.items():
        tip_stat.calc()

    return tip_stats
