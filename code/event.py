import config
import logging
import time
import utils
from bitcoinrpc.authproxy import JSONRPCException


class Event:

    def __init__(self, context):
        self.context = context

    def execute(self):
        try:
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
                    tick_duration = current_time - start_time
                    logging.info('The tick started at {} and took {}s to finish'.format(start_time, tick_duration))

                    if current_time < next_tick:
                        difference = next_tick - current_time
                        logging.info('Sleep {} seconds for next tick'.format(difference))
                        utils.sleep(difference)
                    else:
                        logging.error('Events took {}s to execute.'
                                      ' Consider to raise the tick_duration which is currently {}s.'
                                      .format(current_time - next_tick,
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
        elif cmd_parts[0] == 'block':
            node = self.context.all_bitcoin_nodes[cmd_parts[1]]
            try:
                block_hash = node.execute_rpc('generate', 1)
                logging.info('Created block with hash={}'.format(block_hash))
            except JSONRPCException as exce:
                logging.info('Could not generate block for node={}. Exception="{}"'.format(node.name, exce.message))
        elif len(cmd) == 0:
            pass
        else:
            raise SimulationException('Unknown cmd={} in {}-file'.format(cmd_parts[0], config.ticks_csv))


class SimulationException(Exception):
    pass
