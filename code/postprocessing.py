from clistats import CliStats
from parse import Parser
import config
import bash
import re
import logging
from filewriter import FileWriter
from cmd import rcmd
from cmd import dockercmd
import utils
from multiprocessing.dummy import Pool as ThreadPool


class PostProcessing:
    def __init__(self, context):
        self.context = context

    def execute(self):
        cli_stats = CliStats(self.context)
        cli_stats.execute()

        self.clean_up_docker()

        self.grep_log_for_errors()

        self.aggregate_logs()
        self.cut_log()

        parser = Parser(self.context)
        parser.execute()

        self.update_parsed_blocks()

        file_writer = FileWriter(self.context)
        file_writer.execute()

        bash.check_output(rcmd.create_report(self.context.path.postprocessing_dir))
        logging.info('Report created')

        logging.info('Executed post processing')

    def aggregate_logs(self):
        for node in self.context.all_nodes.values():
            lines = node.cat_log_cmd().splitlines()
            lines = prefix_log(lines, node.name)
            lines = add_line_number(lines)

            with open(self.context.path.aggregated_log, 'a') as file:
                file.write('\n'.join(lines) + '\n')

        lines = bash.check_output_without_log('cat {}'.format(config.log_file)).splitlines()
        lines = add_line_number(lines)
        with open(self.context.path.aggregated_log, 'a') as file:
            file.write('\n'.join(lines) + '\n')

        bash.check_output('sort {} -o {}'.format(self.context.path.aggregated_log, self.context.path.aggregated_log))

    def clean_up_docker(self):
        pool = ThreadPool(10)
        pool.map(rm_node, self.context.all_nodes.values())
        pool.close()
        logging.info('Removed all nodes')

        utils.sleep(3 + len(self.context.all_nodes) * 0.2)

        bash.check_output(dockercmd.rm_network())
        logging.info('Deleted docker network')

        bash.check_output(dockercmd.fix_data_dirs_permissions(self.context.path.sim_dir))
        logging.info('Fixed permissions of dirs used by docker')

    def grep_log_for_errors(self):
        with open(self.context.path.log_errors_txt, 'a') as file:
            for node in self.context.all_nodes.values():
                file.write('{}:\n\n'.format(node.name))
                file.write('{}\n\n\n'.format(node.grep_log_for_errors()))

            file.write('Simcoin:\n\n')
            lines = bash.check_output_without_log(config.log_error_grep.format(config.log_file))
            file.write('{}\n\n\n'.format(lines))
        logging.info('Grepped all logs for errors and saved matched lines to {}'
                     .format(self.context.path.log_errors_txt))

    def update_parsed_blocks(self):
        for block in self.context.parsed_blocks.values():
            block.stale = 'Stale'
            if block.block_hash in self.context.consensus_chain:
                block.stale = 'Accepted'

    def cut_log(self):
        with open(self.context.path.aggregated_log, 'r') as aggregated_log:
            with open(self.context.path.aggregated_sim_log, 'w') as aggregated_sim_log:
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
        logging.info('Aggregated logs')


def rm_node(node):
    node.rm()


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


def add_line_number(lines):
    prefixed_lines = []
    line_number = 0
    for line in lines:
        prefixed_lines.append(re.sub(config.log_prefix_timestamp + ' ([a-zA-Z0-9-\.]+) (.*)',
                                     r'\1 \2 {} \3'.format(line_number), line))
        line_number += 1
    return prefixed_lines
