import config
import re
from datetime import datetime
import logging
import numpy as np
from utils import Stats


class Analyzer:
    def __init__(self, blocks, consensus_chain, txs, tx_exceptions):
        self.blocks = blocks
        self.consensus_chain = consensus_chain
        self.txs = txs
        self.tx_exceptions = tx_exceptions

    def execute(self):
        self.create_block_csv()
        self.create_tx_csv()

        logging.info('Executed analyzer')

    def create_block_csv(self):
        with open(config.blocks_csv, 'w') as file:
            file.write('block_hash;node;timestamp;stale;height;total_size;txs;'
                       'total_received;median_propagation;std_propagation\n')
            for block in self.blocks.values():

                propagation_stats = Stats.from_array(block.receiving_timestamps)

                stale = True
                if block.block_hash in self.consensus_chain:
                    stale = False

                file.write('{};{};{};{};{};{};{};{};{};{}\n'.format(
                    block.block_hash, block.node, block.timestamp, stale, block.height, block.total_size, block.txs,
                    propagation_stats.count, propagation_stats.median, propagation_stats.std))

    def create_tx_csv(self):
        with open(config.tx_csv, 'w') as file:
            file.write('tx_hash;node;timestamp;total_accepted;median_propagation;std_propagation\n')

            for tx in self.txs.values():
                propagation_stats = Stats.from_array(tx.receiving_timestamps)

                file.write('{};{};{};{};{};{}\n'.format(
                    tx.tx_hash, tx.node, tx.timestamp,
                    propagation_stats.count, propagation_stats.median, propagation_stats.std))

    def create_tx_exceptions_csv(self):
        with open(config.tx_exceptions_csv, 'w') as file:
            file.write('node;timestamp;error_message\n')

            for exce in self.tx_exceptions:
                file.write('{};{};{}\n'.format(exce.node, exce.timestamp, exce.error_message))
