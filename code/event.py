import config
import logging
import time
import json
import utils
import subprocess
import threading
import queue


class Event:

    def __init__(self, executor, interval_duration):
        self.executor = executor
        self.interval_duration = interval_duration

    def execute(self):
        exce_queue = queue.Queue()
        with open(config.intervals_csv, 'r') as file:

            for line in file.readlines():

                start_time = time.time()
                cmds = line.split(';')
                threads = []
                for cmd in cmds:
                    thread = self.create_thread(cmd, exce_queue)

                    thread.daemon = True
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()

                if exce_queue.empty() is False:
                    raise Exception('One or more exception occurred during the execution of line {}'.format(line))

                next_interval = start_time + self.interval_duration
                current_time = time.time()
                if current_time < next_interval:
                    difference = next_interval - current_time
                    logging.info('Sleep {} seconds for next interval.'.format(difference))
                    utils.sleep(difference)
                else:
                    raise Exception('Current_time={} is higher then next_interval={}.'
                                    ' Consider to raise the interval_duration which is currently {}s.'
                                    .format(current_time, next_interval, self.interval_duration))

    def create_thread(self, cmd, exce_queue):
        return threading.Thread(target=execute_cmd, args=(cmd, self.executor.all_bitcoin_nodes, exce_queue))


def execute_cmd(cmd, nodes, exce_queue):
    try:
        cmd_parts = cmd.split(' ')
        node = nodes[cmd_parts[1].rstrip()]
        if cmd_parts[0] == 'block':
            generate_block_and_save_creator(node)
        elif cmd_parts[0] == 'tx':
            generate_tx_and_save_creator(node, node.spent_to_address)
        else:
            exce_queue.put(Exception('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.intervals_csv)))
    except Exception as exception:
        exce_queue.put(exception)


def generate_block_and_save_creator(node):
    blocks_string = node.generate_block()
    blocks = json.loads(blocks_string)
    with open(config.blocks_csv, 'a') as file:
        file.write('{};{}\n'.format(node.name, blocks[0]))
    node.mined_blocks += 1


def generate_tx_and_save_creator(node, address):
    try:
        tx_hash = node.generate_tx(address)
        with open(config.tx_csv, 'a') as file:
            file.write('{};{}\n'.format(node.name, tx_hash))
    except subprocess.CalledProcessError:
        logging.info('Could not generate tx for node {}'.format(node.name))
