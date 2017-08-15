from clistats import CliStats
from parse import Parser
import config
import bash
import re
import logging
from analyze import Analyzer


class PostProcessing:
    def __init__(self, context):
        self.context = context

    def execute(self):
        aggregate_logs([node for node in self.context.all_nodes.values()])
        cut_log()
        logging.info('Aggregated logs')

        cli_stats = CliStats(self.context)
        cli_stats.execute()

        parser = Parser(self.context)
        parser.execute()
        logging.info('Executed parsing')

        analyzer = Analyzer(parser.blocks, cli_stats.consensus_chain, parser.txs)
        analyzer.execute()
        logging.info('Executed analyzing')

        logging.info('Executed post processing')


def aggregate_logs(nodes):
    for node in nodes:
        content = bash.check_output_without_log(node.cat_log_cmd()).splitlines()

        content = prefix_log(content, node.name)

        with open(config.aggregated_log, 'a') as file:
            file.write('\n'.join(content) + '\n')

    bash.check_output('cat {} >> {}'.format(config.log_file, config.aggregated_log))
    bash.check_output('sort {} -o {}'.format(config.aggregated_log, config.aggregated_log))


def prefix_log(lines, node_name):
    prev_match = ''
    prefixed_lines = []
    for line in lines:
        match = re.match(config.log_prefix_timestamp, line)
        if match:
            prefixed_lines.append(re.sub(config.log_prefix_timestamp
                                         , r'\1 {}'.format(node_name)
                                         , line))
            prev_match = match.group(0)
        else:
            prefixed_lines.append('{} {} {}'.format(prev_match, node_name, line))
    return prefixed_lines


def cut_log():
    with open(config.aggregated_log, 'r') as aggregated_log:
        with open(config.aggregated_sim_log, 'w') as aggregated_sim_log:
            write = False
            for line in aggregated_log.readlines():
                if write:
                    if config.log_line_sim_end in line:
                        aggregated_sim_log.write(line)
                        break
                    else:
                        aggregated_sim_log.write(line)
                if config.log_line_sim_start in line:
                    aggregated_sim_log.write(line)
                    write = True
