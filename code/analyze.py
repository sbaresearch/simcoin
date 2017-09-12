import config
import logging
import csv
import json
import time
from parse import ReceivedEvent
from parse import BlockStats
from parse import TxStats
from parse import Exce
from parse import Tick
from parse import Mempool
from parse import RPCException


class Analyzer:
    def __init__(self, context):
        self.context = context
        self.tag = context.general_infos['tag']

    def execute(self):

        self.check_block_stale_or_accepted()
        write_csv(config.blocks_csv, BlockStats.csv_header(), self.context.parsed_blocks)
        write_csv(config.txs_csv, TxStats.csv_header(), self.context.parsed_txs)
        write_csv(config.tx_exceptions_csv, Exce.csv_header(), self.context.tx_exceptions)
        write_csv(config.block_exceptions_csv, Exce.csv_header(), self.context.block_exceptions)
        write_csv(config.tick_infos_csv, Tick.csv_header(), self.context.tick_infos)
        write_csv(config.mempool_snapshots_csv, Mempool.csv_header(), self.context.mempool_snapshots)
        write_csv(config.rpc_exceptions_csv, RPCException.csv_header(), self.context.rpc_exceptions)
        write_csv(config.blocks_received_csv, ReceivedEvent.csv_header(), self.context.blocks_received)
        write_csv(config.txs_received_csv, ReceivedEvent.csv_header(), self.context.txs_received)

        self.create_general_infos_json()

        logging.info('Executed analyzer')

    def check_block_stale_or_accepted(self):
        for block in self.context.parsed_blocks.values():
            block.stale = 'Stale'
            if block.block_hash in self.context.consensus_chain:
                block.stale = 'Accepted'

    def create_mempool_snapshots_csv(self):
        with open(config.mempool_snapshots_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['timestamp', 'node', 'txs', 'inputs'])

            for snapshot in self.context.mempool_snapshots:
                w.writerow([snapshot.timestamp, snapshot.node, snapshot.txs, snapshot.inputs])

    def create_rpc_exceptions_csv(self):
        with open(config.rpc_exceptions_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['timestamp', 'node', 'method', 'exception'])

            for exce in self.context.rpc_exceptions:
                w.writerow([exce.timestamp, exce.node, exce.method, exce.exception])

    def create_general_infos_json(self):
        self.context.general_infos['postprocessing_end'] = time.time()
        with open(config.general_infos_json, 'w') as file:
            file.write('{}\n'.format(json.dumps(self.context.general_infos)))


def write_csv(file, header, elements):
    with open(file, 'w') as file:
        w = csv.writer(file, delimiter=';')
        w.writerow(header)

        for element in elements:
            w.writerow(element.vars_to_array())
