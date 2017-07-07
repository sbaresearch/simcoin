import config
import bash
import re
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

    def aggregate_logs(self):
        for node in self.executor.all_nodes.values():
            content = bash.check_output_without_log(node.cat_log_cmd())

            content = prefix_log(content, node.name)

            with open(config.aggregated_log, 'a') as file:
                file.writelines(content)

        bash.check_output('cat {} >> {}'.format(config.log_file, config.aggregated_log))
        bash.check_output('sort {} -o {}'.format(config.aggregated_log, config.aggregated_log))

    def update_blocks_csv(self):
        with open(config.blocks_csv, 'r+') as file:
            lines = file.readlines()
            file.seek(0)
            file.truncate()
            iter_lines = iter(lines)
            first_line = next(iter_lines)
            file.write(first_line.rstrip() + ';mine_time;stale_block;size;number_of_tx;'
                                             'number_of_reached_nodes;'
                                             'blocks_propagation_median;blocks_propagation_std\n')

            for line in iter_lines:
                tokens = line.split(';')
                node = self.executor.all_bitcoin_nodes[tokens[0].rstrip()]
                block_hash = tokens[1].rstrip()

                stale = True
                if block_hash in self.consensus_chain:
                    stale = False

                time = node.block_is_new_tip(block_hash)
                propagation_stats = self.block_propagation(node.name, block_hash, time)

                block = json.loads(node.get_block(block_hash))
                line = line.rstrip()
                line += ';{};{};{};{};{};{};{}\n'\
                    .format(time, stale, block['size'], len(block['tx']),
                            np.size(propagation_stats['values']),
                            propagation_stats['median'],
                            propagation_stats['std'])
                file.write(line)

    def node_stats(self):
        with open(config.nodes_csv, 'w') as file:
            file.write('name;mined_blocks;'
                       'total_tips;total_tips_median_branchlen;tips_std_branchlen;'
                       'valid_headers;valid_headers_median_branchlen;valid_headers_std_branchlen;'
                       'valid_fork;valid_fork_median_branchlen;valid_fork_std_branchlen;\n')
            for node in self.executor.all_bitcoin_nodes.values():
                tips = json.loads(node.get_chain_tips())

                tips_stats = tips_statistics(tips)

                total = tips_stats['total']
                headers = tips_stats['valid-headers']
                fork = tips_stats['valid-fork']
                file.write('{};{};'
                           '{};{};{};'
                           '{};{};{};'
                           '{};{};{}\n'
                           .format(node.name, node.mined_blocks,
                                   total['size'], total['median'], total['std'],
                                   headers['size'], headers['median'], headers['std'],
                                   fork['size'], fork['median'], fork['std']))

    def block_propagation(self, source_node_name, block_hash, mine_time):
        arrive_times = []

        for node in self.executor.all_bitcoin_nodes.values():
            if source_node_name != node.name:
                arrived = node.block_is_new_tip(block_hash)
                if arrived >= 0:
                    arrive_times.append(arrived - mine_time)
        propagation_stats = {'values': np.array(arrive_times)}

        values = propagation_stats['values']
        if len(values) == 0:
            propagation_stats['median'] = float('nan')
            propagation_stats['std'] = float('nan')
        else:
            propagation_stats['median'] = np.median(values)
            propagation_stats['std'] = np.std(values)

        return propagation_stats


def prefix_log(lines, node_name):
    prev_match = ''
    prefixed_lines = []
    for line in lines:
        match = re.match(config.log_timestamp_regex, line)
        if match:
            prefixed_lines.append(re.sub(config.log_timestamp_regex
                                  , r'\1 {}'.format(node_name)
                                  , line))
            prev_match = match.group(0)
        else:
            prefixed_lines.append('{} {} {}'.format(prev_match, node_name, line))
    return prefixed_lines


def tips_statistics(tips):
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

    tips_info = median_std(tips_info)
    return tips_info


def median_std(tips_info):
    for key in tips_info.keys():
        tips_info[key]['size'] = np.size(tips_info[key]['values'])

        if tips_info[key]['size'] > 0:
            tips_info[key]['median'] = np.median(tips_info[key]['values'])
            tips_info[key]['std'] = np.std(tips_info[key]['values'])
        else:
            tips_info[key]['median'] = float('nan')
            tips_info[key]['std'] = float('nan')
    return tips_info
