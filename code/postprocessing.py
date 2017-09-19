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
import subprocess


class PostProcessing:
    def __init__(self, context):
        self.context = context

    def execute(self):
        cli_stats = CliStats(self.context)
        cli_stats.execute()

        self.clean_up_docker()

        self.grep_log_for_errors()

        logging.info(config.log_line_run_end + self.context.run_name)
        flush_log_handlers()
        extract_from_file(config.log_file, self.context.path.run_log,
                          config.log_line_run_start + self.context.run_name,
                          config.log_line_run_end + self.context.run_name)
        self.aggregate_logs()
        extract_from_file(self.context.path.aggregated_log, self.context.path.aggregated_sim_log,
                          config.log_line_sim_start, config.log_line_sim_end)

        parser = Parser(self.context)
        parser.execute()

        self.update_parsed_blocks()
        self.collect_general_infos()

        file_writer = FileWriter(self.context)
        file_writer.execute()

        bash.check_output(rcmd.create_report(self.context.path.postprocessing_dir, config.report_file_name))
        logging.info('Created {} report in folder={}'
                     .format(config.report_file_name, self.context.path.postprocessing_dir))

        logging.info('Executed post processing')

    def aggregate_logs(self):
        for node in self.context.all_nodes.values():
            lines = node.cat_log_cmd().splitlines()
            lines = prefix_log(lines, node.name)
            lines = add_line_number(lines)

            with open(self.context.path.aggregated_log, 'a') as file:
                file.write('\n'.join(lines) + '\n')
            logging.debug('Prefixed and added {:,} lines from node={} to aggregated log'.format(len(lines), node.name))

        lines = bash.check_output_without_log('cat {}'.format(self.context.path.run_log)).splitlines()
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

        bash.check_output(dockercmd.fix_data_dirs_permissions(self.context.path.run_dir))
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

    def collect_general_infos(self):
        self.context.general_infos['current_commit'] = try_cmd('git log -n 1 --pretty=format:"%H"')
        self.context.general_infos['total_memory'] = try_cmd('cat /proc/meminfo | sed -n 1p | grep -ohE [0-9]+')
        self.context.general_infos['cpu_model'] = try_cmd("lscpu | grep -oP 'Model name:\s+\K(.*)'")
        self.context.general_infos['cpus'] = try_cmd("lscpu | grep -oP 'CPU\(s\):\s+\K([0-9]+)$'")


def flush_log_handlers():
    for handler in logging.getLogger().handlers:
        handler.flush()
    logging.debug('Flushed all logging handlers')


def extract_from_file(source, destination, start, end):
    with open(source, 'r') as source_file:
        with open(destination, 'w') as destination_file:
            write = False
            for line in source_file.readlines():
                if write:
                    if end in line:
                        destination_file.write(line)
                        break
                    else:
                        destination_file.write(line)
                if start in line:
                    destination_file.write(line)
                    write = True
    logging.debug('Extracted from file={} lines between start={} and end={} into file {}'
                  .format(source, destination, start, end))


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


def try_cmd(cmd):
    try:
        return bash.check_output(cmd)
    except subprocess.CalledProcessError:
        return 'cmd={} failed'.format(cmd)
