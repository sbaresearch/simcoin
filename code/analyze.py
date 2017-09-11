import config
import logging
from utils import Stats
import csv
import json
import time
from parse import ReceivedEvent


class Analyzer:
    def __init__(self, context):
        self.context = context

    def execute(self):

        self.create_block_csv()
        self.create_tx_csv()
        self.create_tx_csv()
        self.create_tx_exceptions_csv()
        self.create_block_exceptions_csv()
        self.create_tick_infos_csv()
        self.create_mempool_snapshots_csv()
        self.create_rpc_exceptions_csv()
        self.create_general_infos_json()
        write_csv(config.blocks_received_csv, ReceivedEvent.csv_header(), self.context.blocks_received)
        write_csv(config.txs_received_csv, ReceivedEvent.csv_header(), self.context.txs_received)

        logging.info('Executed analyzer')

    def create_block_csv(self):
        with open(config.blocks_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['block_hash', 'node', 'timestamp', 'stale', 'height', 'total_size', 'txs'])
            for block in self.context.parsed_blocks.values():
                stale = 'Stale'
                if block.block_hash in self.context.consensus_chain:
                    stale = 'Accepted'

                w.writerow([block.block_hash, block.node, block.timestamp, stale, block.height, block.total_size,
                            block.txs])

    def create_tx_csv(self):
        with open(config.txs_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['tx_hash', 'node', 'timestamp'])

            for tx in self.context.parsed_txs.values():
                w.writerow([tx.tx_hash, tx.node, tx.timestamp])

    def create_tx_exceptions_csv(self):
        with open(config.tx_exceptions_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['node', 'timestamp', 'exception'])

            for exce in self.context.tx_exceptions:
                w.writerow([exce.node, exce.timestamp, exce.exception])

    def create_block_exceptions_csv(self):
        with open(config.block_exceptions_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['node', 'timestamp', 'exception'])

            for exce in self.context.block_exceptions:
                w.writerow([exce.node, exce.timestamp, exce.exception])

    def create_tick_infos_csv(self):
        with open(config.tick_infos_csv, 'w') as file:
            w = csv.writer(file, delimiter=';')
            w.writerow(['timestamp', 'start', 'duration'])

            for tick in self.context.tick_infos:
                w.writerow([tick.timestamp, tick.start, tick.duration])

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
