import config
import re
from datetime import datetime
import logging
from collections import namedtuple
import pytz


class Parser:
    def __init__(self, context):
        self.context = context
        self.nodes_create_blocks = {node.name: None for node in context.all_bitcoin_nodes.values()}
        self.parsers = [
            self.block_creation_parser,
            self.tip_updated_parser,
            self.block_received_parser,
            self.block_reconstructed_parser,
            self.tx_creation_parser,
            self.tx_received_parser,
            self.peer_logic_validation_parser,
            self.tick_parser,
            self.tx_exception_parser,
            self.block_exception_parser,
            self.rpc_exception_parser,
        ]

        logging.info('Created parser with {} log parsers'.format(len(self.parsers)))

    def execute(self):
        with open(config.aggregated_sim_log, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                for parser in self.parsers:
                    try:
                        parser(line)
                        break
                    except ParseException:
                        pass
                if (i + 1) % 100000 == 0:
                    logging.info('Parsed {} of {} log lines'.format(i + 1, len(lines)))
        logging.info('Executed parser')

    def block_creation_parser(self, line):
        create_new_block = parse_create_new_block(line)

        self.nodes_create_blocks[create_new_block.node] = create_new_block

    def tip_updated_parser(self, line):
        update_tip = parse_update_tip(line)

        create_new_block = self.nodes_create_blocks[update_tip.node]
        if create_new_block is not None:
            block_stats = BlockEvent(create_new_block.timestamp, create_new_block.node, update_tip.block_hash,
                                     create_new_block.total_size, create_new_block.txs)
            block_stats.height = update_tip.height
            self.context.parsed_blocks[update_tip.block_hash] = block_stats
            self.nodes_create_blocks[update_tip.node] = None
        else:
            if update_tip.block_hash in self.context.parsed_blocks:
                block_stats = self.context.parsed_blocks[update_tip.block_hash]
                block_stats.height = update_tip.height

    def block_received_parser(self, line):
        received_event = parse_received_block(line)
        block = self.context.parsed_blocks[received_event.obj_hash]
        received_event.propagation_duration = received_event.timestamp - block.timestamp

        self.context.blocks_received.append(received_event)

    def block_reconstructed_parser(self, line):
        received_event = parse_successfully_reconstructed_block(line)
        block = self.context.parsed_blocks[received_event.obj_hash]
        received_event.propagation_duration = received_event.timestamp - block.timestamp

        self.context.blocks_received.append(received_event)

    def tx_creation_parser(self, line):
        log_line_with_hash = parse_add_to_wallet(line)

        self.context.parsed_txs[log_line_with_hash.obj_hash] = TxEvent(log_line_with_hash.timestamp,
                                                                       log_line_with_hash.node,
                                                                       log_line_with_hash.obj_hash)

    def tx_received_parser(self, line):
        received_event = parse_accept_to_memory_pool(line)
        tx = self.context.parsed_txs[received_event.obj_hash]
        received_event.propagation_duration = received_event.timestamp - tx.timestamp

        self.context.txs_received.append(received_event)

    def peer_logic_validation_parser(self, line):
        log_line_with_hash = parse_peer_logic_validation(line)
        create_new_block = self.nodes_create_blocks[log_line_with_hash.node]

        if create_new_block is not None:

            block_stats = BlockEvent(create_new_block.timestamp, create_new_block.node, log_line_with_hash.obj_hash,
                                     create_new_block.total_size, create_new_block.txs)
            self.context.parsed_blocks[block_stats.block_hash] = block_stats
            self.nodes_create_blocks[log_line_with_hash.node] = None

    def tick_parser(self, line):
        self.context.tick_infos.append(
            parse_tick_log_line(line)
        )

    def tx_exception_parser(self, line):
        self.context.tx_exceptions.append(
            parse_tx_creation_exception(line)
        )

    def block_exception_parser(self, line):
        self.context.block_exceptions.append(
            parse_block_creation_exception(line)
        )

    def rpc_exception_parser(self, line):
        self.context.rpc_exceptions.append(
            parse_rpc_exception(line)
        )


def parse_create_new_block(line):
    regex = config.log_prefix_full + 'CreateNewBlock\(\): total size: ([0-9]+)' \
                                     ' block weight: [0-9]+ txs: ([0-9]+) fees: [0-9]+ sigops [0-9]+$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'CreateNewBlock' log line.")

    return CreateNewBlockEvent(
        parse_datetime(matched.group(1)),
        str(matched.group(2)),
        int(matched.group(3)),
        int(matched.group(4)),
    )


def parse_update_tip(line):
    regex = config.log_prefix_full + 'UpdateTip: new best=([0-9,a-z]{64}) height=([0-9]+) version=0x[0-9]{8}' \
                                     ' log2_work=[0-9]+\.?[0-9]* tx=([0-9]+)' \
                                     ' date=\'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\'' \
                                     ' progress=[0-9]+.[0-9]+ cache=[0-9]+\.[0-9]+[a-zA-Z]+\([0-9]+txo?\)$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'CreateNewBlock' log line.")

    return UpdateTipEvent(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)),
                          int(matched.group(4)), int(matched.group(5)))


def parse_received_block(line):
    regex = config.log_prefix_full + 'received block ([a-z0-9]{64}) peer=[0-9]+$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'Received block' log line.")

    return ReceivedEvent(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)))


def parse_successfully_reconstructed_block(line):
    regex = config.log_prefix_full + 'Successfully reconstructed block ([a-z0-9]{64}) ' \
                                     'with ([0-9]+) txn prefilled, ([0-9]+) txn from mempool' \
                                     ' \(incl at least ([0-9]+) from extra pool\) and [0-9]+ txn requested$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'Reconstructed block' log line.")

    return ReceivedEvent(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)))


def parse_add_to_wallet(line):
    regex = config.log_prefix_full + 'AddToWallet ([a-z0-9]{64})  new$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'AddToWallet' log line.")

    return EventWithHash(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)))


def parse_accept_to_memory_pool(line):
    regex = config.log_prefix_full + 'AcceptToMemoryPool: peer=([0-9]+):' \
                                     ' accepted ([0-9a-z]{64}) \(poolsz ([0-9]+) txn,' \
                                     ' ([0-9]+) [a-zA-Z]+\)$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'AcceptToMemoryPool' log line.")

    return ReceivedEvent(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(4)))


def parse_peer_logic_validation(line):
    regex = config.log_prefix_full + 'PeerLogicValidation::NewPoWValidBlock ' \
                                     'sending header-and-ids ([a-z0-9]{64}) ' \
                                     'to peer=[0-9]+'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'PeerLogicValidation' log line.")

    return EventWithHash(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)))


def parse_tick_log_line(line):
    regex = config.log_prefix_full + '\[.*\] \[.*\]  The tick started at ([0-9]+\.[0-9]+)' \
                                     ' and took ([0-9]+\.[0-9]+)s to finish$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'Tick' log line.")

    return TickEvent(parse_datetime(matched.group(1)), float(matched.group(3)), float(matched.group(4)))


def parse_tx_creation_exception(line):
    regex = config.log_prefix_full + '\[.*\] \[.*\]  Could not generate tx for node=([a-zA-Z0-9-\.]+)\.' \
                                     ' Exception="(.+)"$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'Tx exception' log line.")

    return ExceptionEvent(parse_datetime(matched.group(1)), str(matched.group(3)), str(matched.group(4)))


def parse_block_creation_exception(line):
    regex = config.log_prefix_full + '\[.*\] \[.*\]  Could not generate block for node=([a-zA-Z0-9-\.]+)\.' \
                                     ' Exception="(.+)"$'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'Block exception' log line.")

    return ExceptionEvent(parse_datetime(matched.group(1)), str(matched.group(3)), str(matched.group(4)))


def parse_rpc_exception(line):
    regex = config.log_prefix_full + '\[.*\] \[.*\]  Node=([a-zA-Z0-9-\.]+) could not execute RPC-call=([a-zA-Z0-9]+)' \
                                     ' because of error="(.*)"\. Reconnecting RPC and retrying.'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'RPC exception' log line.")

    return RPCExceptionEvent(parse_datetime(matched.group(1)), str(matched.group(3)), str(matched.group(4)),
                             str(matched.group(5)))


def parse_datetime(date_time):
    parsed_date_time = datetime.strptime(date_time, config.log_time_format)
    return parsed_date_time.replace(tzinfo=pytz.UTC).timestamp()


CreateNewBlockEvent = namedtuple('CreateNewBlockLogLine', 'timestamp node  total_size txs')

UpdateTipEvent = namedtuple('UpdateTipLogLine', 'timestamp node block_hash height tx')

EventWithHash = namedtuple('LogLineWithHash', 'timestamp node obj_hash')


class Event:
    def __init__(self, timestamp, node):
        self.timestamp = timestamp
        self.node = node


class RPCExceptionEvent(Event):
    def __init__(self, timestamp, node, method, exception):
        super().__init__(timestamp, node)
        self.method = method
        self.exception = exception

    @staticmethod
    def csv_header():
        return ['timestamp', 'node', 'method', 'exception']

    def vars_to_array(self):
        return [self.timestamp, self.node, self.method, self.exception]


class ExceptionEvent(Event):
    def __init__(self, timestamp, node, exception):
        super().__init__(timestamp, node)
        self.exception = exception

    @staticmethod
    def csv_header():
        return ['timestamp', 'node', 'exception']

    def vars_to_array(self):
        return [self.timestamp, self.node, self.exception]


class ReceivedEvent(Event):
    def __init__(self, timestamp, node, obj_hash):
        super().__init__(timestamp, node)
        self.obj_hash = obj_hash
        self.propagation_duration = -1

    @staticmethod
    def csv_header():
        return ['timestamp', 'node', 'obj_hash', 'propagation_duration']

    def vars_to_array(self):
        return [self.timestamp, self.node, self.obj_hash, self.propagation_duration]


class BlockEvent(Event):
    def __init__(self, timestamp, node, block_hash, total_size, txs):
        super().__init__(timestamp, node)
        self.block_hash = block_hash
        self.stale = None
        self.total_size = total_size
        self.txs = txs
        self.height = -1

    @staticmethod
    def csv_header():
        return ['timestamp', 'node', 'block_hash', 'stale', 'total_size', 'txs', 'height']

    def vars_to_array(self):
        return [self.timestamp, self.node, self.block_hash, self.stale, self.total_size, self.txs, self.height]


class TxEvent(Event):

    def __init__(self, timestamp, node, tx_hash):
        super().__init__(timestamp, node)
        self.tx_hash = tx_hash

    @staticmethod
    def csv_header():
        return ['timestamp', 'node', 'tx_hash']

    def vars_to_array(self):
        return [self.timestamp, self.node, self.tx_hash]


class TickEvent:
    def __init__(self, timestamp, start, duration):
        self.timestamp = timestamp
        self.start = start
        self.duration = duration

    @staticmethod
    def csv_header():
        return ['timestamp', 'start', 'duration']

    def vars_to_array(self):
        return [self.timestamp, self.start, self.duration]


class ParseException(Exception):
    pass
