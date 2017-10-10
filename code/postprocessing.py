from clistats import CliStats
from parse import Parser
import config
import bash
import logging
from cmd import rcmd
from cmd import dockercmd
import utils
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import subprocess
import json
from runner import StepTimes
import time
import csv


class PostProcessing:
    def __init__(self, context, writer):
        self.context = context
        self.writer = writer
        self.pool = None
        self.thread_pool = None

    def execute(self):
        self.pool = Pool(config.pool_processors)
        self.thread_pool = ThreadPool(5)

        cli_stats = CliStats(self.context, self.writer)
        cli_stats.execute()

        self.clean_up_docker()

        logging.info(config.log_line_run_end + self.context.run_name)
        flush_log_handlers()
        extract_from_file(config.log_file, config.run_log,
                          config.log_line_run_start + self.context.run_name,
                          config.log_line_run_end + self.context.run_name)

        parser = Parser(self.context, self.writer)
        parser.execute()

        collect_general_infos()

        self.context.step_times.append(StepTimes(time.time(), 'postprocessing_end'))
        self.writer.write_csv(config.step_times_csv_file_name, StepTimes.csv_header, self.context.step_times)

        bash.check_output(rcmd.create_report(config.postprocessing_dir, config.report_file_name))
        logging.info('Created {} report in folder={}'
                     .format(config.report_file_name, config.postprocessing_dir))

        self.pool.close()
        self.thread_pool.close()
        logging.info('Executed post processing')

    def clean_up_docker(self):
        self.thread_pool.map(self.rm_node, self.context.all_nodes.values())
        logging.info('Removed all nodes')

        utils.sleep(3 + len(self.context.all_nodes) * 0.2)

        bash.check_output(dockercmd.rm_network())
        logging.info('Deleted docker network')

        bash.check_output(dockercmd.fix_data_dirs_permissions(self.context.run_dir))
        logging.info('Fixed permissions of dirs used by docker')

    @staticmethod
    def rm_node(node):
        node.rm()


def collect_general_infos():
    general_infos = {
        'total_memory': try_cmd('cat /proc/meminfo | sed -n 1p | grep -ohE [0-9]+'),
        'cpu_model': try_cmd("lscpu | grep -oP 'Model name:\s+\K(.*)'"),
        'cpus': try_cmd("lscpu | grep -oP 'CPU\(s\):\s+\K([0-9]+)$'"),
    }

    with open(config.general_infos_csv, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(general_infos.keys())
        writer.writerow(general_infos.values())


def flush_log_handlers():
    for handler in logging.getLogger().handlers:
        handler.flush()
    logging.debug('Flushed all logging handlers')


def extract_from_file(source, destination, start, end):
    with open(source, 'r') as source_file:
        with open(destination, 'w') as destination_file:
            write = False
            for line in source_file:
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


def try_cmd(cmd):
    try:
        return bash.check_output(cmd)
    except subprocess.CalledProcessError:
        return 'cmd={} failed'.format(cmd)
