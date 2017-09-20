import config
import re
from datetime import datetime
import logging
from collections import namedtuple
import pytz
from multiprocessing.dummy import Pool as ThreadPool
import utils
from itertools import repeat


class Parser:
    def __init__(self, context):
        self.context = context
        self.nodes_create_blocks = {node.name: None for node in context.all_bitcoin_nodes.values()}
        self.parsed_blocks = {}
        self.parsers = [
            self.block_creation_parser,
            self.tip_updated_parser,
            self.peer_logic_validation_parser,
        ]
        self.pool = ThreadPool(5)

        logging.info('Created parser with {} log parsers'.format(len(self.parsers)))

    def execute(self):
        self.execute1()
        self.execute2()
        self.pool.close()
        logging.info('Finished parsing aggregated log={}'.format(self.context.path.aggregated_sim_log))

    def execute1(self):
        with open(self.context.path.aggregated_sim_log, 'r') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                for parser in self.parsers:
                    try:
                        parser(line)
                        break
                    except ParseException:
                        pass
                if (i + 1) % 100000 == 0:
                    logging.info('Parsed {:,} of {:,} log lines'.format(i + 1, len(lines)))

            utils.write_csv(
                self.context.path.postprocessing_dir + BlockEvent.file_name,
                BlockEvent.csv_header,
                self.parsed_blocks.values(),
                self.context.args.tag
            )
            logging.info('Block parser parsed {} events out of {} lines from {} into file {}'
                         .format(len(self.parsed_blocks.values()), len(lines), self.context.path.aggregated_sim_log,
                                 BlockEvent.file_name))

    def execute2(self):
        self.pool.starmap(parse, zip(
            repeat(self.context.path.aggregated_sim_log),
            [
                BlockReceivedEvent, BlockExceptionEvent,
                TxEvent, TxReceivedEvent, TxExceptionEvent,
                TickEvent, RPCExceptionEvent
            ],
            repeat(self.context.path.postprocessing_dir),
            repeat(self.context.args.tag)

        ))

    def block_creation_parser(self, line):
        create_new_block = parse_create_new_block(line)

        self.nodes_create_blocks[create_new_block.node] = create_new_block

    def tip_updated_parser(self, line):
        update_tip = parse_update_tip(line)

        create_new_block = self.nodes_create_blocks[update_tip.node]
        if create_new_block is not None:
            block_event = BlockEvent(create_new_block.timestamp, create_new_block.node, update_tip.block_hash,
                                     create_new_block.total_size, create_new_block.txs)
            block_event.height = update_tip.height
            self.parsed_blocks[update_tip.block_hash] = block_event
            self.nodes_create_blocks[update_tip.node] = None
        else:
            if update_tip.block_hash in self.parsed_blocks:
                block_event = self.parsed_blocks[update_tip.block_hash]
                block_event.height = update_tip.height

    def peer_logic_validation_parser(self, line):
        log_line_with_hash = parse_peer_logic_validation(line)
        create_new_block = self.nodes_create_blocks[log_line_with_hash.node]

        if create_new_block is not None:

            block_event = BlockEvent(create_new_block.timestamp, create_new_block.node, log_line_with_hash.obj_hash,
                                     create_new_block.total_size, create_new_block.txs)
            self.parsed_blocks[block_event.block_hash] = block_event
            self.nodes_create_blocks[log_line_with_hash.node] = None


def parse(log_file, cls, postprocessing_dir, tag):
    parsed_objects = []
    with open(log_file, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            try:
                parsed_objects.append(cls.from_log_line(line))
            except ParseException:
                pass
            if (i + 1) % 100000 == 0:
                logging.info('{} parser parsed {:,} of {:,} log lines'.format(cls.__name__, i + 1, len(lines)))

    utils.write_csv(postprocessing_dir + cls.file_name, cls.csv_header, parsed_objects, tag)
    logging.info('{} parser parsed {} events out of {} lines from {} into file {}'
                 .format(cls.__name__, len(parsed_objects), len(lines), log_file, cls.file_name))


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
        raise ParseException("Didn't matched 'UpdateTip' log line.")

    return UpdateTipEvent(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)),
                          int(matched.group(4)), int(matched.group(5)))


def parse_peer_logic_validation(line):
    regex = config.log_prefix_full + 'PeerLogicValidation::NewPoWValidBlock ' \
                                     'sending header-and-ids ([a-z0-9]{64}) ' \
                                     'to peer=[0-9]+'
    matched = re.match(regex, line)

    if matched is None:
        raise ParseException("Didn't matched 'PeerLogicValidation' log line.")

    return EventWithHash(parse_datetime(matched.group(1)), str(matched.group(2)), str(matched.group(3)))


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


class BlockEvent(Event):
    csv_header = ['timestamp', 'node', 'hash', 'total_size', 'txs', 'height']
    file_name = 'blocks.csv'

    def __init__(self, timestamp, node, block_hash, total_size, txs):
        super().__init__(timestamp, node)
        self.block_hash = block_hash
        self.total_size = total_size
        self.txs = txs
        self.height = -1

    def vars_to_array(self):
        return [self.timestamp, self.node, self.block_hash, self.total_size, self.txs, self.height]


class TxEvent(Event):
    csv_header = ['timestamp', 'node', 'hash']
    file_name = 'txs.csv'

    def __init__(self, timestamp, node, tx_hash):
        super().__init__(timestamp, node)
        self.tx_hash = tx_hash

    @classmethod
    def from_log_line(cls, line):
        matched = re.match(config.log_prefix_full + 'AddToWallet ([a-z0-9]{64})  new$', line)

        if matched is None:
            raise ParseException("Didn't matched 'AddToWallet' log line.")

        return cls(parse_datetime(
            matched.group(1)),
            str(matched.group(2)),
            str(matched.group(3))
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.tx_hash]


class TickEvent:
    csv_header = ['timestamp', 'start', 'duration']
    file_name = 'tick_infos.csv'

    def __init__(self, timestamp, start, duration):
        self.timestamp = timestamp
        self.start = start
        self.duration = duration

    @classmethod
    def from_log_line(cls, line):
        match = re.match(
            config.log_prefix_full + '\[.*\] \[.*\]  The tick started at ([0-9]+\.[0-9]+)'
                                     ' and took ([0-9]+\.[0-9]+)s to finish$',
            line)
        if match is None:
            raise ParseException("Didn't matched 'Tick' log line.")

        return cls(
            parse_datetime(match.group(1)),
            float(match.group(3)),
            float(match.group(4))
        )

    def vars_to_array(self):
        return [self.timestamp, self.start, self.duration]


class ReceivedEvent(Event):
    csv_header = ['timestamp', 'node', 'hash']

    def __init__(self, timestamp, node, obj_hash):
        super().__init__(timestamp, node)
        self.obj_hash = obj_hash

    def vars_to_array(self):
        return [self.timestamp, self.node, self.obj_hash]


class BlockReceivedEvent(ReceivedEvent):
    file_name = 'blocks_received.csv'

    @classmethod
    def from_log_line(cls, line):
        regexs = [
            'Successfully reconstructed block ([a-z0-9]{64}) with ([0-9]+) txn prefilled,'
            ' ([0-9]+) txn from mempool \(incl at least ([0-9]+) from extra pool\) and'
            ' [0-9]+ txn requested$',
            'received block ([a-z0-9]{64}) peer=[0-9]+$'
        ]

        matched = None
        for regex in regexs:
            matched = re.match(config.log_prefix_full + regex, line)

            if matched is not None:
                break

        if matched is None:
            raise ParseException("Didn't matched 'Reconstructed block' log line.")

        return cls(
            parse_datetime(matched.group(1)),
            str(matched.group(2)),
            str(matched.group(3))
        )


class TxReceivedEvent(ReceivedEvent):
    file_name = 'txs_received.csv'

    @classmethod
    def from_log_line(cls, line):
        matched = re.match(config.log_prefix_full +
                           'AcceptToMemoryPool: peer=([0-9]+): accepted ([0-9a-z]{64}) \(poolsz ([0-9]+) txn,'
                           ' ([0-9]+) [a-zA-Z]+\)$', line)

        if matched is None:
            raise ParseException("Didn't matched 'AcceptToMemoryPool' log line.")

        return cls(
            parse_datetime(matched.group(1)),
            str(matched.group(2)),
            str(matched.group(4))
        )


class ExceptionEvent(Event):
    csv_header = ['timestamp', 'node', 'exception']

    def __init__(self, timestamp, node, exception):
        super().__init__(timestamp, node)
        self.exception = exception

    def vars_to_array(self):
        return [self.timestamp, self.node, self.exception]


class BlockExceptionEvent(ExceptionEvent):
    file_name = 'block_exceptions.csv'

    @classmethod
    def from_log_line(cls, line):
        matched = re.match(config.log_prefix_full +
                           '\[.*\] \[.*\]  Could not generate block for node=([a-zA-Z0-9-.]+)\.'
                           ' Exception="(.+)"$', line)

        if matched is None:
            raise ParseException("Didn't matched 'Block exception' log line.")

        return cls(parse_datetime(
            matched.group(1)),
            str(matched.group(3)),
            str(matched.group(4))
        )


class TxExceptionEvent(ExceptionEvent):
    file_name = 'tx_exceptions.csv'

    @classmethod
    def from_log_line(cls, line):
        matched = re.match(config.log_prefix_full +
                           '\[.*\] \[.*\]  Could not generate tx for node=([a-zA-Z0-9-.]+)\.'
                           ' Exception="(.+)"$', line)

        if matched is None:
            raise ParseException("Didn't matched 'Tx exception' log line.")

        return cls(parse_datetime(
            matched.group(1)),
            str(matched.group(3)),
            str(matched.group(4))
        )


class RPCExceptionEvent(Event):
    csv_header = ['timestamp', 'node', 'method', 'exception']
    file_name = 'rpc_exceptions.csv'

    def __init__(self, timestamp, node, method, exception):
        super().__init__(timestamp, node)
        self.method = method
        self.exception = exception

    @classmethod
    def from_log_line(cls, line):
        matched = re.match(config.log_prefix_full +
                           '\[.*\] \[.*\]  Node=([a-zA-Z0-9-\.]+) could not execute RPC-call=([a-zA-Z0-9]+)' \
                           ' because of error="(.*)"\. Reconnecting RPC and retrying.', line)

        if matched is None:
            raise ParseException("Didn't matched 'RPC exception' log line.")

        return cls(
            parse_datetime(matched.group(1)),
            str(matched.group(3)),
            str(matched.group(4)),
            str(matched.group(5))
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.method, self.exception]


class ParseException(Exception):
    pass
