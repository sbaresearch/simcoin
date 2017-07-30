import config
import re
from datetime import datetime
import logging
import numpy as np
import stats


class Parser:
    def __init__(self, node_names):
        self.nodes_create_blocks = {node_name: None for node_name in node_names}
        self.blocks = {}
        self.tx = {}

        self.parsers = [
            self.block_creation_parser,
            self.tip_updated_parser,
            self.block_received_parser,
            self.block_reconstructed_parser,
            self.tx_creation_parser,
        ]

    def parse_aggregated_sim_log(self):
        with open(config.aggregated_sim_log, 'r') as file:
            lines = file.readlines()
            for line in lines:
                for parser in self.parsers:
                    try:
                        parser(line)
                        break
                    except ParseException:
                        logging.debug("Parsers couldn't parse line")

    def create_block_csv(self):
        with open(config.blocks_csv, 'w') as file:
            file.write('block_hash;node;timestamp;height;total_size;txs;'
                       'total_received;median_propagation;std_propagation\n')
            for block in self.blocks.values():
                block_stats = stats.calc_median_std(block.receiving_timestamps)

                file.write('{};{};{};{};{};{};{};{};{}\n'.format(
                    block.block_hash, block.node, block.timestamp, block.height, block.total_size, block.txs,
                    block_stats['len'], block_stats['median'], block_stats['std']))

    def block_creation_parser(self, line):
        create_new_block = parse_create_new_block(line)

        self.nodes_create_blocks[create_new_block.node] = create_new_block

    def tip_updated_parser(self, line):
        update_tip = parse_update_tip(line)
        create_new_block = self.nodes_create_blocks[update_tip.node]

        if create_new_block is not None:
            block_stats = BlockStats(create_new_block.timestamp, create_new_block.node, update_tip.block_hash,
                                     update_tip.height, create_new_block.total_size, create_new_block.txs)
            self.blocks[block_stats.block_hash] = block_stats
            self.nodes_create_blocks[update_tip.node] = None

    def block_received_parser(self, line):
        received_block = parse_received_block(line)

        block_stats = self.blocks[received_block.obj_hash]

        block_stats.receiving_timestamps = np.append(block_stats.receiving_timestamps, received_block.timestamp)

    def block_reconstructed_parser(self, line):
        received_block = parse_successfully_reconstructed_block(line)

        block_stats = self.blocks[received_block.obj_hash]

        block_stats.receiving_timestamps = np.append(block_stats.receiving_timestamps, received_block.timestamp)

    def tx_creation_parser(self,line):
        log_line_with_hash = parse_add_to_wallet(line)

        self.tx[log_line_with_hash.obj_hash] = TxStats(log_line_with_hash.timestamp,
                                                       log_line_with_hash.node, log_line_with_hash.obj_hash)

    def tx_received_parser(self, line):
        log_line_with_hash = parse_accept_to_memory_pool(line)

        tx_stats = self.tx[log_line_with_hash.obj_hash]
        tx_stats.receiving_timestamps = np.append(tx_stats.receiving_timestamps, log_line_with_hash.timestamp)


def parse_create_new_block(line):
    regex = config.log_prefix_full + 'CreateNewBlock\(\): total size: ([0-9]+)' \
                                ' block weight: [0-9]+ txs: ([0-9]+) fees: [0-9]+ sigops [0-9]+$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched CreateNewBlock log line.")

    return CreateNewBlock(
        datetime.strptime(matched.group(1), config.log_time_format).timestamp(),
        str(matched.group(2)),
        int(matched.group(3)),
        int(matched.group(4)),
    )


def parse_update_tip(line):
    regex = config.log_prefix_full + 'UpdateTip: new best=([0-9,a-z]{64}) height=([0-9]+) version=0x[0-9]{8}' \
                                ' log2_work=[0-9]+\.?[0-9]* tx=([0-9]+)' \
                                ' date=\'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\'' \
                                ' progress=[0-9]+.[0-9]+ cache=[0-9]+\.[0-9]+[a-zA-Z]+\([0-9]+tx\)$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched CreateNewBlock log line.")

    return UpdateTip(
        datetime.strptime(matched.group(1), config.log_time_format).timestamp(),
        str(matched.group(2)),
        str(matched.group(3)),
        int(matched.group(4)),
        int(matched.group(5)),
    )


def parse_received_block(line):
    regex = config.log_prefix_full + 'received block ([a-z0-9]{64}) peer=[0-9]+$'

    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched Received block log line.")

    return LogLineWithHash(
        datetime.strptime(matched.group(1), config.log_time_format).timestamp(),
        str(matched.group(2)),
        str(matched.group(3)),
    )


def parse_successfully_reconstructed_block(line):
    regex = config.log_prefix_full + 'Successfully reconstructed block ([a-z0-9]{64}) ' \
                                     'with ([0-9]+) txn prefilled, ([0-9]+) txn from mempool' \
                                     ' \(incl at least ([0-9]+) from extra pool\) and [0-9]+ txn requested$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched Successfully reconstructed block log line.")

    return LogLineWithHash(
        datetime.strptime(matched.group(1), config.log_time_format).timestamp(),
        str(matched.group(2)),
        str(matched.group(3)),
    )


def parse_add_to_wallet(line):
    regex = config.log_prefix_full + 'AddToWallet ([a-z0-9]{64})  new$'

    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't AddToWallet log line.")

    return LogLineWithHash(
        datetime.strptime(matched.group(1), config.log_time_format).timestamp(),
        str(matched.group(2)),
        str(matched.group(3)),
    )


def parse_accept_to_memory_pool(line):
    regex = config.log_prefix_full + 'AcceptToMemoryPool: peer=([0-9]+):' \
                                     ' accepted ([0-9a-z]{64}) \(poolsz ([0-9]+) txn,' \
                                     ' ([0-9]+) [a-zA-Z]+\)$'

    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't AddToWallet log line.")

    return LogLineWithHash(
        datetime.strptime(matched.group(1), config.log_time_format).timestamp(),
        str(matched.group(2)),
        str(matched.group(4)),
    )


def cut_log():
    with open(config.aggregated_log, 'r') as aggregated_log:
        with open(config.aggregated_sim_log, 'w') as aggregated_sim_log:
            write = False
            for line in aggregated_log.readlines():
                if write:
                    if config.log_line_sim_end in line:
                        aggregated_sim_log.write(line)
                        break
                    else:
                        aggregated_sim_log.write(line)
                if config.log_line_sim_start in line:
                    aggregated_sim_log.write(line)
                    write = True


class LogLine:
    def __init__(self, timestamp, node):
        self.timestamp = timestamp
        self.node = node


class CreateNewBlock(LogLine):
    def __init__(self, timestamp, node, total_size, txs):
        super().__init__(timestamp, node)
        self.total_size = total_size
        self.txs = txs


class UpdateTip(LogLine):
    def __init__(self, timestamp, node, block_hash, height, txs):
        super().__init__(timestamp, node)
        self.block_hash = block_hash
        self.height = height
        self.txs = txs


class LogLineWithHash(LogLine):
    def __init__(self, timestamp, node, obj_hash):
        super().__init__(timestamp, node)
        self.obj_hash = obj_hash


class BlockStats:
    def __init__(self, timestamp, node, block_hash, height, total_size, txs):
        self.timestamp = timestamp
        self.node = node
        self.block_hash = block_hash
        self.height = height
        self.total_size = total_size
        self.txs = txs
        self.receiving_timestamps = np.array([])


class TxStats:

    def __init__(self, timestamp, node, tx_hash):
        self.timestamp = timestamp
        self.node = node
        self.tx_hash = tx_hash
        self.receiving_timestamps = np.array([])


class ParseException(Exception):
    pass
