import config
import logging
import time
import utils
import subprocess


class Event:

    def __init__(self, executor, tick_duration):
        self.executor = executor
        self.tick_duration = tick_duration

    def execute(self):
        utils.check_for_file(config.ticks_csv)
        with open(config.ticks_csv, 'r') as file:

            for line in file.readlines():

                start_time = time.time()
                cmds = line.split(';')
                for cmd in cmds:
                    execute_cmd(cmd, self.executor.all_bitcoin_nodes)
                next_tick = start_time + self.tick_duration
                current_time = time.time()
                if current_time < next_tick:
                    difference = next_tick - current_time
                    logging.info('Sleep {} seconds for next tick.'.format(difference))
                    utils.sleep(difference)
                else:
                    raise Exception('Current_time={} is higher then next_tick={}.'
                                    ' Consider to raise the tick_duration which is currently {}s.'
                                    .format(current_time, next_tick, self.tick_duration))


def execute_cmd(cmd, nodes):
    cmd_parts = cmd.split(' ')
    node = nodes[cmd_parts[1].rstrip()]
    if cmd_parts[0] == 'block':
        node.generate_block()
    elif cmd_parts[0] == 'tx':
        generate_tx(node, node.spent_to_address)
    else:
        raise Exception('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.ticks_csv))


def generate_tx(node, address):
    try:
        node.generate_tx(address)
    except subprocess.CalledProcessError:
        logging.info('Could not generate tx for node {}'.format(node.name))
