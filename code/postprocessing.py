from clistats import CliStats
from parse import Parser
import config
import bash
import re
import logging
from cmd import rcmd
from cmd import dockercmd
import utils
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import subprocess
import itertools
import json
from runner import StepTimes
import time
import fcntl


class PostProcessing:
    def __init__(self, context):
        self.context = context
        self.pool = Pool(config.pool_processors)
        self.thread_pool = ThreadPool(5)

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

        collect_general_infos(self.context.path.general_infos_json)

        self.context.step_times.append(StepTimes(time.time(), 'postprocessing_end'))
        utils.write_csv(self.context.path.step_times, StepTimes.csv_header(), self.context.step_times, self.context.args.tag)

        bash.check_output(rcmd.create_report(self.context.path.postprocessing_dir, config.report_file_name))
        logging.info('Created {} report in folder={}'
                     .format(config.report_file_name, self.context.path.postprocessing_dir))

        self.pool.close()
        logging.info('Executed post processing')

    def aggregate_logs(self):
        self.pool.starmap(prefix_and_copy_log, zip(
            [node.path + config.bitcoin_log_file_name
             for node in self.context.all_nodes.values()] + [self.context.path.run_log],
            [node.name for node in self.context.all_nodes.values()] + ['simcoin'],
            itertools.repeat(self.context.path.aggregated_log)))

        bash.check_output('sort {} -o {}'.format(self.context.path.aggregated_log, self.context.path.aggregated_log))

    def clean_up_docker(self):
        self.thread_pool.map(rm_node, self.context.all_nodes.values())
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


def collect_general_infos(path):
    general_infos = {
        'current_commit': try_cmd('git log -n 1 --pretty=format:"%H"'),
        'total_memory': try_cmd('cat /proc/meminfo | sed -n 1p | grep -ohE [0-9]+'),
        'cpu_model': try_cmd("lscpu | grep -oP 'Model name:\s+\K(.*)'"),
        'cpus': try_cmd("lscpu | grep -oP 'CPU\(s\):\s+\K([0-9]+)$'"),
    }

    with open(path, 'w') as file:
        file.write('{}\n'.format(json.dumps(general_infos)))


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


def prefix_and_copy_log(log, name, aggregated_log):
    with open(log) as log_file:
        lines = log_file.readlines()
        logging.info('Read {:,} lines from node={}'.format(len(lines), name))

        lines = prefix_log(lines, name)
        logging.info('Prefixed {:,} lines from node={}'.format(len(lines), name))

        with open(aggregated_log, 'a') as aggregated_log_file:
            logging.debug('Waiting for lock to write log from node={} to file={}'.format(name, aggregated_log))
            fcntl.flock(aggregated_log_file, fcntl.LOCK_EX)
            logging.debug('Received lock for writing log from node={} to file={}'.format(name, aggregated_log))

            aggregated_log_file.write('\n'.join(lines) + '\n')

            fcntl.flock(aggregated_log_file, fcntl.LOCK_UN)
    logging.debug('Wrote {:,} lines from node={} to aggregated log'.format(len(lines), name))


def prefix_log(lines, node_name):
    prev_match = ''
    prefixed_lines = []
    line_number = 1
    for line in lines:
        match = re.match(config.log_prefix_timestamp, line)
        if match:
            prefixed_lines.append(re.sub(config.log_prefix_timestamp
                                         , r'\1 {} {}'.format(node_name, line_number)
                                         , line))
            prev_match = match.group(0)
        else:
            prefixed_lines.append('{} {} {} {}'.format(prev_match, node_name, line_number, line))
        line_number += 1
    return prefixed_lines


def add_line_number(lines):
    prefixed_lines = []
    line_number = 1
    for line in lines:
        prefixed_lines.append(re.sub(config.log_prefix_timestamp + ' ([a-zA-Z0-9-.]+) (.*)',
                                     r'\1 \2 {} \3'.format(line_number), line))
        line_number += 1
    return prefixed_lines


def try_cmd(cmd):
    try:
        return bash.check_output(cmd)
    except subprocess.CalledProcessError:
        return 'cmd={} failed'.format(cmd)
