import config
import utils
import json
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
                    if node.get_block_hash_silent(height) != 0:
                        break
                    blocks.append(node.get_block_hash(height))
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
                height = int(node.get_block_count())
                hashes = []
                while self.executor.first_block_height <= height:
                    hashes.append(str(node.get_block_hash(height)))
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
                tips = json.loads(node.get_chain_tips())

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
                                   total['len'], total['median'], total['std'],
                                   headers['len'], headers['median'], headers['std'],
                                   fork['len'], fork['median'], fork['std'],
                                   headers_only['len'], headers_only['median'], headers_only['std']))


def calc_median_std(values):
    stats = {'len': len(values), 'values': values}
    if stats['len'] == 0:
        stats['median'] = float('nan')
        stats['std'] = float('nan')
    else:
        stats['median'] = np.median(values)
        stats['std'] = np.std(values)

    return stats


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

    return {'valid-headers': calc_median_std(np.array(valid_headers)),
            'valid-fork': calc_median_std(np.array(valid_fork)),
            'headers-only': calc_median_std(np.array(headers_only)),
            'total': calc_median_std(np.array(valid_fork + valid_headers))}
