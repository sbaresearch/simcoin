import config
import re
from datetime import datetime
import logging
import pytz
from multiprocessing import Pool
from itertools import repeat
from chunker import Chunker


class Parser:
    def __init__(self, context, writer):
        self.context = context
        self.writer = writer
        self.pool = Pool(config.pool_processors)

        logging.info('Created parser with host={} and node={} log parsers'
                     .format(len(host_parsers), len(node_parsers)))

    def execute(self):

        for parser in host_parsers + node_parsers:
            self.writer.write_header_csv(parser.file_name, parser.csv_header)
        logging.info('Created all empty csv files')

        self.pool.starmap(parse, zip(
            repeat(self.writer,),
            repeat(self.context.path.run_log),
            repeat('simcoin'),
            Chunker.chunkify(self.context.path.run_log, config.file_chunk_size),
            repeat(host_parsers),
        ))

        for node in self.context.all_bitcoin_nodes.values():
            self.pool.starmap(parse, zip(
                repeat(self.writer),
                repeat(node.get_log_file()),
                repeat(node.name),
                Chunker.chunkify(node.get_log_file(), config.file_chunk_size),
                repeat(node_parsers),
            ))

        self.pool.close()
        logging.info('Finished parsing aggregated log={}'.format(self.context.path.aggregated_sim_log))


def parse(writer, log_file, name, chunk, parsers):
    parsed_objects = {}
    for line in Chunker.parse(Chunker.read(log_file, chunk)):
        for parser in parsers:
            try:
                parsed_object = parser.from_log_line(line, name)
                parsed_objects.setdefault(parsed_object.file_name, []).append(parsed_object)
                break
            except ParseException:
                pass

    for key in parsed_objects:
        writer.append_csv(key, parsed_objects[key])
    logging.info('Parsed {} event types out of chunk {} from file={}'
                 .format(len(parsed_objects), chunk, log_file, log_file))


def parse_datetime(date_time):
    parsed_date_time = datetime.strptime(date_time, config.log_time_format)
    return parsed_date_time.replace(tzinfo=pytz.UTC).timestamp()


class Event:
    def __init__(self, timestamp, node):
        self.timestamp = timestamp
        self.node = node


class BlockCreateEvent(Event):
    csv_header = ['timestamp', 'node', 'total_size', 'txs']
    file_name = 'blocks_create.csv'

    def __init__(self, timestamp, node, total_size, txs):
        super().__init__(timestamp, node)
        self.total_size = total_size
        self.txs = txs

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(
            config.log_prefix_timestamp + 'CreateNewBlock\(\): total size: ([0-9]+) block weight: [0-9]+ txs: ([0-9]+)'
                                          ' fees: [0-9]+ sigops [0-9]+$', line)

        if match is None:
            raise ParseException("Didn't match 'CreateNewBlock' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            int(match.group(2)),
            int(match.group(3)),
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.total_size, self.txs]


class UpdateTipEvent(Event):
    csv_header = ['timestamp', 'node', 'hash', 'height', 'tx']
    file_name = 'update_tip.csv'

    def __init__(self, timestamp, node, block_hash, height, tx):
        super().__init__(timestamp, node)
        self.block_hash = block_hash
        self.height = height
        self.tx = tx

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(
            config.log_prefix_timestamp + 'UpdateTip: new best=([0-9,a-z]{64}) height=([0-9]+) version=0x[0-9]{8}'
                                          ' log2_work=[0-9]+\.?[0-9]* tx=([0-9]+)'
                                          ' date=\'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\''
                                          ' progress=[0-9]+.[0-9]+ cache=[0-9]+\.[0-9]+[a-zA-Z]+\([0-9]+txo?\)$', line)

        if match is None:
            raise ParseException("Didn't match 'UpdateTip' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(2)),
            int(match.group(3)),
            int(match.group(4))
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.block_hash, self.height, self.tx]


class PeerLogicValidationEvent(Event):
    csv_header = ['timestamp', 'node', 'hash']
    file_name = 'peer_logic_validation.csv'

    def __init__(self, timestamp, node, block_hash):
        super().__init__(timestamp, node)
        self.block_hash = block_hash

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(
            config.log_prefix_timestamp + 'PeerLogicValidation::NewPoWValidBlock sending header-and-ids ([a-z0-9]{64}) '
                                          'to peer=[0-9]+', line)

        if match is None:
            raise ParseException("Didn't match 'PeerLogicValidation' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(2))
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.block_hash]


class TxEvent(Event):
    csv_header = ['timestamp', 'node', 'hash']
    file_name = 'txs.csv'

    def __init__(self, timestamp, node, tx_hash):
        super().__init__(timestamp, node)
        self.tx_hash = tx_hash

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp + 'AddToWallet ([a-z0-9]{64})  new$', line)

        if match is None:
            raise ParseException("Didn't match 'AddToWallet' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(2)),
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.tx_hash]


class TickEvent:
    csv_header = ['timestamp', 'source', 'number', 'start', 'duration']
    file_name = 'tick_infos.csv'

    def __init__(self, timestamp, source, number, start, duration):
        self.timestamp = timestamp
        self.source = source
        self.number = number
        self.start = start
        self.duration = duration

    @classmethod
    def from_log_line(cls, line, source):
        match = re.match(
            config.log_prefix_timestamp + '\[.*\] \[.*\]  Tick=([0-9]+) started at ([0-9]+\.[0-9]+)'
                                          ' and took ([0-9]+\.[0-9]+)s to finish$',
            line)
        if match is None:
            raise ParseException("Didn't match 'Tick' log line.")

        return cls(
            parse_datetime(match.group(1)),
            source,
            int(match.group(2)),
            float(match.group(3)),
            float(match.group(4))
        )

    def vars_to_array(self):
        return [self.timestamp, self.source, self.number, self.start, self.duration]


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
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp + 'received block ([a-z0-9]{64}) peer=[0-9]+$', line)

        if match is None:
            raise ParseException("Didn't match 'Received block' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(2)),
        )


class BlockReconstructEvent(ReceivedEvent):
    file_name = 'blocks_reconstructed.csv'

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(
            config.log_prefix_timestamp + 'Successfully reconstructed block ([a-z0-9]{64}) with ([0-9]+) txn prefilled,'
                                          ' ([0-9]+) txn from mempool \(incl at least ([0-9]+) from extra pool\) and'
                                          ' [0-9]+ txn requested$', line)
        if match is None:
            raise ParseException("Didn't match 'Reconstructed block' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(2)),
        )


class TxReceivedEvent(ReceivedEvent):
    file_name = 'txs_received.csv'

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp +
                         'AcceptToMemoryPool: peer=([0-9]+): accepted ([0-9a-z]{64}) \(poolsz ([0-9]+) txn,'
                         ' ([0-9]+) [a-zA-Z]+\)$', line)

        if match is None:
            raise ParseException("Didn't match 'AcceptToMemoryPool' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(3)),
        )


class ExceptionEvent(Event):
    csv_header = ['timestamp', 'node', 'source', 'exception']

    def __init__(self, timestamp, node, source, exception):
        super().__init__(timestamp, node)
        self.exception = exception
        self.source = source

    def vars_to_array(self):
        return [self.timestamp, self.node, self.source, self.exception]


class BlockExceptionEvent(ExceptionEvent):
    file_name = 'block_exceptions.csv'

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp +
                         '\[.*\] \[.*\]  Could not generate block for node=([a-zA-Z0-9-.]+)\.'
                         ' Exception="(.+)"$', line)

        if match is None:
            raise ParseException("Didn't match 'Block exception' log line.")

        return cls(
            parse_datetime(match.group(1)),
            str(match.group(2)),
            node,
            str(match.group(3))
        )


class TxExceptionEvent(ExceptionEvent):
    file_name = 'tx_exceptions.csv'

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp +
                         '\[.*\] \[.*\]  Could not generate tx for node=([a-zA-Z0-9-.]+)\.'
                         ' Exception="(.+)"$', line)

        if match is None:
            raise ParseException("Didn't match 'Tx exception' log line.")

        return cls(
            parse_datetime(match.group(1)),
            str(match.group(2)),
            node,
            str(match.group(3))
        )


class RPCExceptionEvent(Event):
    csv_header = ['timestamp', 'node', 'source', 'method', 'exception']
    file_name = 'rpc_exceptions.csv'

    def __init__(self, timestamp, node, source, method, exception):
        super().__init__(timestamp, node)
        self.source = source
        self.method = method
        self.exception = exception

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp +
                         '\[.*\] \[.*\]  Node=([a-zA-Z0-9-\.]+) could not execute RPC-call=([a-zA-Z0-9]+)'
                         ' because of error="(.*)"\. Reconnecting RPC and retrying.', line)

        if match is None:
            raise ParseException("Didn't match 'RPC exception' log line.")

        return cls(
            parse_datetime(match.group(1)),
            str(match.group(2)),
            node,
            str(match.group(3)),
            str(match.group(4))
        )

    def vars_to_array(self):
        return [self.timestamp, self.node, self.source, self.method, self.exception]


class ParseException(Exception):
    pass


node_parsers = [
    BlockCreateEvent,
    BlockReceivedEvent,
    BlockReconstructEvent,
    UpdateTipEvent,
    PeerLogicValidationEvent,

    TxEvent,
    TxReceivedEvent,
]

host_parsers = [
    TxExceptionEvent,
    BlockExceptionEvent,
    RPCExceptionEvent,

    TickEvent,
]
