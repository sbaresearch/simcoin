import config
import re
from datetime import datetime
import logging
import pytz
from multiprocessing import Pool
from itertools import repeat
from chunker import Chunker
import write


class Parser:
    def __init__(self, context, writer):
        self._context = context
        self._writer = writer
        self._pool = None

        logging.info('Created parser with host={} and node={} log parsers'
                     .format(len(host_parsers), len(node_parsers)))

    def execute(self):
        self._pool = Pool(config.pool_processors)

        for parser in host_parsers + node_parsers:
            write.write_header_csv(parser.file_name, parser.csv_header)
        logging.info('Created all empty csv files')

        self._pool.starmap(parse, zip(
            repeat(self._writer,),
            repeat(config.run_log),
            repeat('simcoin'),
            Chunker.chunkify(config.run_log, config.file_chunk_size),
            repeat(host_parsers),
        ))

        for node in self._context.nodes.values():
            self._pool.starmap(parse, zip(
                repeat(self._writer),
                repeat(node.get_log_file()),
                repeat(node.name),
                Chunker.chunkify(node.get_log_file(), config.file_chunk_size),
                repeat(node_parsers),
            ))

        self._pool.close()
        logging.info('Finished parsing of run_log and all node logs')


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
    csv_header = ['timestamp', 'node']

    def __init__(self, timestamp, node):
        self._timestamp = timestamp
        self._node = node

    def vars_to_array(self):
        return [self._timestamp, self._node]


class BlockCreateEvent(Event):
    csv_header = Event.csv_header + ['hash']
    file_name = 'blocks_create_raw.csv'
    file_name_after_R_preprocessing = 'blocks_create.csv'

    def __init__(self, timestamp, node, _hash):
        super().__init__(timestamp, node)
        self._hash = _hash

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(
            config.log_prefix_timestamp + 'Simcoin CreateNewBlock\(\): hash:([0-9,a-z]{64})$', line)

        if match is None:
            raise ParseException("Didn't match 'CreateNewBlock' log line.")

        return cls(
            parse_datetime(match.group(1)),
            node,
            str(match.group(2)),
        )

    def vars_to_array(self):
        return Event.vars_to_array(self) + [self._hash]


class BlockStatsEvent(Event):
    csv_header = Event.csv_header + ['total_size', 'txs']
    file_name = 'blocks_stats_raw.csv'
    file_name_after_R_preprocessing = 'blocks_stats.csv'

    def __init__(self, timestamp, node, total_size, txs):
        super().__init__(timestamp, node)
        self._total_size = total_size
        self._txs = txs

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
        return Event.vars_to_array(self) + [self._total_size, self._txs]


class UpdateTipEvent(Event):
    csv_header = Event.csv_header + ['hash', 'height', 'tx']
    file_name = 'update_tip_raw.csv'
    file_name_after_R_preprocessing = 'update_tip.csv'

    def __init__(self, timestamp, node, _hash, height, tx):
        super().__init__(timestamp, node)
        self._hash = _hash
        self._height = height
        self._tx = tx

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
        return Event.vars_to_array(self) + [self._hash, self._height, self._tx]


class PeerLogicValidationEvent(Event):
    csv_header = Event.csv_header + ['hash']
    file_name = 'peer_logic_validation_raw.csv'
    file_name_after_R_preprocessing = 'peer_logic_validation.csv'

    def __init__(self, timestamp, node, _hash):
        super().__init__(timestamp, node)
        self._hash = _hash

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
        return Event.vars_to_array(self) + [self._hash]


class TxEvent(Event):
    csv_header = Event.csv_header + ['hash']
    file_name = 'txs_raw.csv'
    file_name_after_R_preprocessing = 'txs.csv'

    def __init__(self, timestamp, node, _hash):
        super().__init__(timestamp, node)
        self._hash = _hash

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
        return Event.vars_to_array(self) + [self._hash]


class TickEvent:
    csv_header = ['timestamp', 'source', 'number', 'planned_start', 'actual_start', 'duration', 'txs', 'blocks']
    file_name = 'tick_infos.csv'

    def __init__(self, timestamp, source, number, planned_start, actual_start, duration, txs, blocks):
        self._timestamp = timestamp
        self._source = source
        self._number = number
        self._planned_start = planned_start
        self._actual_start = actual_start
        self._duration = duration
        self._txs = txs
        self._blocks = blocks

    @classmethod
    def from_log_line(cls, line, source):
        match = re.match(
            config.log_prefix_timestamp + '\[.*\] \[.*\]  Tick=([0-9]+) with planned_start=([0-9]+\.[0-9]+),'
                                          ' actual_start=([0-9]+\.[0-9]+) and duration=([0-9]+\.[0-9]+),'
                                          ' created txs=([0-9]+) and blocks=([0-9]+)$', line)
        if match is None:
            raise ParseException("Didn't match 'Tick' log line.")

        return cls(
            parse_datetime(match.group(1)),
            source,
            int(match.group(2)),
            float(match.group(3)),
            float(match.group(4)),
            float(match.group(5)),
            int(match.group(6)),
            int(match.group(7)),
        )

    def vars_to_array(self):
        return [self._timestamp, self._source, self._number, self._planned_start, self._actual_start, self._duration,
                self._txs, self._blocks]


class ReceivedEvent(Event):
    csv_header = Event.csv_header + ['hash']

    def __init__(self, timestamp, node, obj_hash):
        super().__init__(timestamp, node)
        self.obj_hash = obj_hash

    def vars_to_array(self):
        return Event.vars_to_array(self) + [self.obj_hash]


class BlockReceivedEvent(ReceivedEvent):
    file_name = 'blocks_received_raw.csv'
    file_name_after_R_preprocessing = 'blocks_received.csv'

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
    file_name = 'blocks_reconstructed_raw.csv'
    file_name_after_R_preprocessing = 'blocks_reconstructed.csv'

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
    file_name = 'txs_received_raw.csv'
    file_name_after_R_preprocessing = 'txs_received.csv'

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
    csv_header = Event.csv_header + ['source', 'exception']

    def __init__(self, timestamp, node, source, exception):
        super().__init__(timestamp, node)
        self._source = source
        self._exception = exception

    def vars_to_array(self):
        return Event.vars_to_array(self) + [self._source, self._exception]


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
    csv_header = Event.csv_header + ['source', 'method', 'exception', 'retries_left']
    file_name = 'rpc_exceptions.csv'

    def __init__(self, timestamp, node, source, method, exception, retries_left):
        super().__init__(timestamp, node)
        self._source = source
        self._method = method
        self._exception = exception
        self._retries_left = retries_left

    @classmethod
    def from_log_line(cls, line, node):
        match = re.match(config.log_prefix_timestamp +
                         '\[.*\] \[.*\]  Could not execute RPC-call=([a-zA-Z0-9]+) on node=([a-zA-Z0-9-\.]+)'
                         ' because of error="(.*)"\. Reconnecting and retrying, ([0-9]+) retries left', line)

        if match is None:
            raise ParseException("Didn't match 'RPC exception' log line.")

        return cls(
            parse_datetime(match.group(1)),
            str(match.group(3)),
            node,
            str(match.group(2)),
            str(match.group(4)),
            int(match.group(5))
        )

    def vars_to_array(self):
        return Event.vars_to_array(self) + [self._source, self._method, self._exception, self._retries_left]


class ParseException(Exception):
    pass


node_parsers = [
    BlockCreateEvent,
    BlockStatsEvent,
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
