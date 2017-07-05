import config
import bash
import re
import logging
import utils
import json
import numpy as np


class Stats:
    def __init__(self, _executor):
        self.executor = _executor
        self.consensus_chain = []

    def save_consensus_chain(self):
        with open(config.consensus_chain_csv, 'w') as file:
            file.write("height;block_hash\n")
            height = self.executor.first_block_height
            while True:
                blocks = []
                for node in self.executor.all_bitcoin_nodes.values():
                    if node.get_block_hash_silent(height) is not 0:
                        break
                    blocks.append(node.get_block_hash(height))
                if len(blocks) > 0 and utils.check_equal(blocks):
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
                file.write('{};{}\n'.format(node.name, '; '.join(hashes)))

    def aggregate_logs(self):
        try:
            for node in self.executor.all_nodes.values():
                bash.check_output('{} > {}'.format(node.cat_log_cmd(), config.tmp_log))

                with open(config.tmp_log) as file:
                    content = file.readlines()

                prev_match = ''
                for i, line in enumerate(content):
                    match = re.match(config.log_timestamp_regex, line)
                    if match:
                        content[i] = re.sub(config.log_timestamp_regex
                                            , r'\1 {}'.format(node.name)
                                            , line)
                        prev_match = match.group(0)
                    else:
                        content[i] = '{} {} {}'.format(prev_match, node.name, line)

                with open(config.aggregated_log, mode='a') as file:
                    file.writelines(content)

            bash.check_output('cat {} >> {}'.format(config.log_file, config.aggregated_log))
            bash.check_output('sort {} -o {}'.format(config.aggregated_log, config.aggregated_log))
        finally:
            bash.check_output('rm {}'.format(config.tmp_log))

    def update_blocks_csv(self):
        with open(config.blocks_csv, 'r+') as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()

            iter_lines = iter(lines)
            first_line = next(iter_lines)
            file.write(first_line.rstrip() + ';stale_block;size;number_of_tx\n')

            for line in iter_lines:
                tokens = line.split(';')
                node = self.executor.all_bitcoin_nodes[tokens[0].rstrip()]
                block_hash = tokens[1].rstrip()

                if block_hash in self.consensus_chain:
                    line = line.rstrip() + ';False'
                else:
                    line = line.rstrip() + ';True'

                block = json.loads(node.get_block(block_hash))
                line += ';{};{}\n'.format(block['size'], len(block['tx']))
                file.write(line)

    def node_stats(self):
        with open(config.nodes_csv, 'w') as file:
            file.write('name;mined_blocks;'
                       'total_tips;total_tips_median_branchlen;tips_std_branchlen;'
                       'valid_headers;valid_headers_median_branchlen;valid_headers_std_branchlen;'
                       'valid_fork;valid_fork_median_branchlen;valid_fork_std_branchlen;\n')
            for node in self.executor.all_bitcoin_nodes.values():
                tips = json.loads(node.get_chain_tips())
                tips_info = {
                    'valid-headers': {'values': np.array([], dtype=np.uint)},
                    'valid-fork': {'values': np.array([], dtype=np.uint)},
                }
                iter_tips = iter(tips)

                # omit first active tip
                next(iter_tips)

                for tip in iter_tips:
                    tips_info[tip['status']]['values'] \
                        = np.append(tips_info[tip['status']]['values'], tip['branchlen'])
                tips_info['total'] \
                    = {'values': np.append(tips_info['valid-headers']['values'], tips_info['valid-fork']['values'])}

                for key in tips_info.keys():
                    tips_info[key]['size'] = np.size(tips_info[key]['values'])

                    if tips_info[key]['size'] > 0:
                        tips_info[key]['median'] = np.median(tips_info[key]['values'])
                        tips_info[key]['std'] = np.std(tips_info[key]['values'])
                    else:
                        tips_info[key]['median'] = float('nan')
                        tips_info[key]['std'] = float('nan')

                total = tips_info['total']
                headers = tips_info['valid-headers']
                fork = tips_info['valid-fork']
                file.write('{};{};'
                           '{};{};{};'
                           '{};{};{};'
                           '{};{};{};\n'
                           .format(node.name, node.mined_blocks,
                                   total['size'], total['median'], total['std'],
                                   headers['size'], headers['median'], headers['std'],
                                   fork['size'], fork['median'], fork['std']))
