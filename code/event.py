import config
import logging
import time
import utils
from bitcoinrpc.authproxy import JSONRPCException
from datetime import datetime
from collections import namedtuple


class Event:

    def __init__(self, context):
        self.context = context

    def execute(self):
        utils.check_for_file(config.ticks_csv)
        with open(config.ticks_csv, 'r') as file:

            for line in file.readlines():
                start_time = time.time()

                line = line.rstrip()
                cmds = line.split(';')
                for cmd in cmds:
                    self.execute_cmd(cmd)
                next_tick = start_time + self.context.args.tick_duration
                current_time = time.time()
                if current_time < next_tick:
                    difference = next_tick - current_time
                    logging.info('Sleep {} seconds for next tick.'.format(difference))
                    utils.sleep(difference)
                else:
                    logging.error('Current_time={} is higher then next_tick={}.'
                                  ' Consider to raise the tick_duration which is currently {}s.'
                                  .format(current_time, next_tick, self.context.args.tick_duration))
                    exit(-1)

    def execute_cmd(self, cmd):
        cmd_parts = cmd.split(' ')

        if cmd_parts[0] == 'tx':
            node = self.context.all_bitcoin_nodes[cmd_parts[1]]

            # generate_tx_rpc is not always successful. eg. miner has not enough money or tx fee calculation fails
            try:
                node.generate_tx()
            except JSONRPCException as exce:
                self.context.tx_exceptions.append(TransactionException(node.name, datetime.now(), exce.message))
                logging.info('Could not generate tx for node {}. Exception={}'.format(node.name, exce.message))

        elif cmd_parts[0] == 'block':
            node = self.context.all_bitcoin_nodes[cmd_parts[1]]
            block_hash = node.execute_rpc('generate', 1)
            logging.info('Created block with hash={}'.format(block_hash))
        elif len(cmd) == 0:
            pass
        else:
            raise Exception('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.ticks_csv))

TransactionException = namedtuple('TransactionException', 'node timestamp error_message')
