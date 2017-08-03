import config
import utils
import numpy as np


class CliStats:
    def __init__(self, _executor):
        self.executor = _executor
        self.consensus_chain = []

    def execute(self):
        self.save_consensus_chain()
        self.save_chains()
        self.node_stats()

    def save_consensus_chain(self):
        with open(config.consensus_chain_csv, 'w') as file:
            file.write("height;block_hash\n")
            height = self.executor.first_block_height
            nodes = self.executor.all_bitcoin_nodes.values()
            while True:
                blocks = []
                for node in nodes:
                    if node.execute_rpc('getblockhash', height) != 0:
                        break
                    blocks.append(node.execute_rpc('getblockhash', height))
                if len(blocks) == len(nodes) and utils.check_equal(blocks):
                    self.consensus_chain.append(blocks[0])
                    file.write('{};{}\n'.format(height, blocks[0]))
                    height += 1
                else:
                    break

    def save_chains(self):
        with open(config.chains_csv, 'w') as file:
            file.write("node;block_hashes\n")
            for node in self.executor.all_bitcoin_nodes.values():
                height = int(node.execute_rpc('getblockcount'))
                hashes = []
                while self.executor.first_block_height <= height:
                    hashes.append(str(node.execute_rpc('getblockhash', height)))
                    height -= 1
                file.write('{};{}\n'.format(node.name, ';'.join(hashes)))

    def node_stats(self):
        with open(config.nodes_csv, 'w') as file:
            file.write('name;'
                       'total_tips;total_tips_median_branchlen;tips_std_branchlen;'
                       'valid_headers;valid_headers_median_branchlen;valid_headers_std_branchlen;'
                       'valid_fork;valid_fork_median_branchlen;valid_fork_std_branchlen;'
                       'headers_only;headers_only_median_branchlen;headers_only_std_branchlen;\n')
            for node in self.executor.all_bitcoin_nodes.values():
                tips = node.execute_rpc('getchaintips')

                tips_stats = tips_statistics(tips)

                total = tips_stats['total']
                headers = tips_stats['valid-headers']
                fork = tips_stats['valid-fork']
                headers_only = tips_stats['headers-only']
                file.write('{};'
                           '{};{};{};'
                           '{};{};{};'
                           '{};{};{};'
                           '{};{};{}\n'
                           .format(node.name,
                                   total.count, total.median, total.std,
                                   headers.count, headers.median, headers.std,
                                   fork.count, fork.median, fork.std,
                                   headers_only.count, headers_only.median, headers_only.std))


def tips_statistics(tips):
    valid_headers = []
    valid_fork = []
    headers_only = []

    for tip in tips:
        if tip['status'] == 'valid-headers':
            valid_headers.append(tip['branchlen'])
        elif tip['status'] == 'valid-fork':
            valid_fork.append(tip['branchlen'])
        elif tip['status'] == 'headers-only':
            headers_only.append(tip['branchlen'])
        elif tip['status'] == 'active':
            # omit active tip
            pass
        else:
            raise Exception('Unknown tip type={}'.format(tip['status']))

    return {'valid-headers': Stats.from_array(np.array(valid_headers)),
            'valid-fork': Stats.from_array(np.array(valid_fork)),
            'headers-only': Stats.from_array(np.array(headers_only)),
            'total': Stats.from_array(np.array(valid_fork + valid_headers))}


class Stats:

    def __init__(self, count, median, std):
        self.count = count
        self.median = median
        self.std = std

    @classmethod
    def from_array(cls, array):
        count = len(array)
        if count == 0:
            median = float('nan')
            std = float('nan')
        else:
            median = np.median(array)
            std = np.std(array)
        return cls(count, median, std)
