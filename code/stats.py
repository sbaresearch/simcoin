import config
import bash
import re
import logging
import utils


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
                    if bash.call_silent(node.get_block_hash(height)) is not 0:
                        break
                    blocks.append(bash.check_output(node.get_block_hash(height), lvl=logging.DEBUG))
                if len(blocks) > 0 and utils.check_equal(blocks):
                    self.consensus_chain.append(blocks[0])
                    file.write('{}; {}\n'.format(height, blocks[0]))
                    height += 1
                else:
                    break

    def save_chains(self):
        with open(config.chains_csv, 'w') as file:
            file.write("node;block_hashes\n")
            for node in self.executor.all_bitcoin_nodes.values():
                height = int(bash.check_output(node.get_block_count(), lvl=logging.DEBUG))
                hashes = []
                while self.executor.first_block_height <= height:
                    hashes.append(str(bash.check_output(node.get_block_hash(height), lvl=logging.DEBUG)))
                    height -= 1
                file.write('{}; {}\n'.format(node.name, '; '.join(hashes)))

    def aggregate_logs(self):
        try:
            for node in self.executor.all_nodes.values():
                bash.check_output('{} > {}'.format(node.cat_log(), config.tmp_log))

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
            file.write(first_line.rstrip() + ';stale_block\n')

            for line in iter_lines:
                block = line.split(';')[1].rstrip()
                if block in self.consensus_chain:
                    line = line.rstrip() + ';False\n'
                else:
                    line = line.rstrip() + ';True\n'
                file.write(line)
