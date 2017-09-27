import config
import logging
import time
import utils
from bitcoinrpc.authproxy import JSONRPCException
import math


class Event:

    def __init__(self, context):
        self.context = context
        self.txs_count = self.blocks_count = 0

    def execute(self):
        try:
            utils.check_for_file(config.ticks_csv)
            with open(config.ticks_csv, 'r') as file:

                for i, line in enumerate(file):
                    start_time = time.time()
                    self.txs_count = self.blocks_count = 0

                    line = line.rstrip()
                    cmds = line.split(',')
                    for cmd in cmds:
                        self.execute_cmd(cmd)

                    next_tick = start_time + self.context.args.tick_duration
                    current_time = time.time()
                    tick_duration = current_time - start_time
                    logging.info('Tick={} from={} to={}, created txs={}, blocks={} and took {}s to finish'
                                 .format(i, start_time, next_tick, self.txs_count, self.blocks_count, tick_duration))

                    if current_time < next_tick:
                        difference = next_tick - current_time
                        logging.info('Sleep {} seconds for next tick={}'.format(difference, i))
                        utils.sleep(difference)
                    else:
                        logging.error('Events in tick={} took {}s to execute.'
                                      ' Consider to raise the tick_duration which is currently {}s.'
                                      .format(i + 1, current_time - next_tick,
                                              self.context.args.tick_duration))
                        raise SimulationException('Events took to long to execute')
        except Exception as exce:
            logging.error('Simulation could not execute all events because of exception={}'.format(exce))

    def execute_cmd(self, cmd):
        cmd_parts = cmd.split(' ')

        if cmd_parts[0] == 'tx':
            node = self.context.all_bitcoin_nodes[cmd_parts[1]]
            try:
                node.generate_tx()
            except JSONRPCException as exce:
                logging.info('Could not generate tx for node={}. Exception="{}"'.format(node.name, exce.message))
            self.txs_count += 1
        elif cmd_parts[0] == 'block':
            node = self.context.all_bitcoin_nodes[cmd_parts[1]]
            try:
                node.generate_block()
            except JSONRPCException as exce:
                logging.info('Could not generate block for node={}. Exception="{}"'.format(node.name, exce.message))
            self.blocks_count += 1
        elif len(cmd) == 0:
            pass
        else:
            raise SimulationException('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.ticks_csv))


def calc_analyze_skip_ticks(blocks_per_tick, tx_per_tick):
    return max([1, math.ceil(1/blocks_per_tick), math.ceil(1/tx_per_tick)])


class SimulationException(Exception):
    pass
